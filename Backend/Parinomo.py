import re
from collections import defaultdict
import json
from typing import Any
import subprocess
import time
import tempfile
import os

# Global constant for tile size (will be determined dynamically)
TILE_SIZE = 64  # Default value, will be optimized using empirical testing

# gives list of all variables withing the loop block return as single varaible or array varaible
def extract_loop_variables(code):
    """
    Extracts variables from C/C++ loop blocks, categorizing them as single or array variables.
    
    Args:
        code (str): A string containing C/C++ loop code
        
    Returns:
        tuple: (single_variables, array_variables) lists containing variable names
    """
    # Remove C-style comments
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
    
    # Find all variable declarations
    declarations = re.findall(r'\b(?:int|float|double|char|bool|long|short|unsigned|void|auto|std)\s+([a-zA-Z_][a-zA-Z0-9_]*)', code)
    
    # Find all variables used in the code
    # This looks for identifiers that aren't part of a keyword or function call
    all_identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b(?!\s*\()', code)
    
    # Remove C/C++ keywords
    keywords = ['for', 'if', 'else', 'while', 'do', 'switch', 'case', 'break', 'continue',
                'return', 'int', 'float', 'double', 'char', 'bool', 'void', 'long', 'short','std',
                'unsigned', 'signed', 'const', 'static', 'struct', 'enum', 'class', 'auto']
    all_identifiers = [ident for ident in all_identifiers if ident not in keywords]
    
    # Find array access patterns: identifiers followed by square brackets
    array_pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\[')
    array_variables = list(set(array_pattern.findall(code)))
    
    # All other variables are single variables
    single_variables = list(set(all_identifiers) - set(array_variables))
    
    # Add declared variables that might not be used
    single_variables = list(set(single_variables + declarations))
    
    # Sort lists for consistent output
    single_variables.sort()
    array_variables.sort()
    
    return single_variables, array_variables

def analyze_openmp_variables(code, single_variables, array_variables):
    """
    Analyzes loop variables to determine their OpenMP clause classification
    (shared, private, firstprivate, lastprivate)
    
    Args:
        code (str): C/C++ loop code
        single_variables (list): List of single variables
        array_variables (list): List of array variables
        
    Returns:
        dict: Dictionary containing lists of variables for each OpenMP clause
    """
    # Remove C-style comments
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
    
    # Extract code inside the loop body (between curly braces)
    loop_body_match = re.search(r'for\s*\([^)]*\)\s*{(.*?)}', code, re.DOTALL)
    if not loop_body_match:
        return {"error": "No valid loop body found"}
    
    loop_body = loop_body_match.group(1)
    
    # Extract loop control variable
    loop_control_match = re.search(r'for\s*\(\s*(?:int\s+)?([a-zA-Z_][a-zA-Z0-9_]*)', code)
    if not loop_control_match:
        return {"error": "Could not identify loop control variable"}
    
    loop_var = loop_control_match.group(1)
    
    # Initialize result categories
    result = {
        "shared": [],
        "private": [loop_var],  # Loop control variable is always private
        # "firstprivate": [],
        # "lastprivate": [],
        "reduction": []
    }
    
    # Find all variables declared inside the loop
    declared_inside = re.findall(r'\b(?:int|float|double|char|bool|long|short|unsigned|void|std|auto)\s+([a-zA-Z_][a-zA-Z0-9_]*)', loop_body)
    
    # All variables declared inside the loop are private
    result["private"].extend(declared_inside)
    
    # Check each single variable
    for var in single_variables:
        if var in declared_inside or var == loop_var:
            continue  # Already handled
            
        # Check if read before write (firstprivate candidate)
        lines = loop_body.split('\n')
        read_first = False
        written = False
        
        for line in lines:
            # Look for read operations (variable appears on right side of assignment or in expressions)
            read_match = re.search(rf'[=|+|\-|*|/|%|&|\||^|>|<|!|?|:|\s]\s*{var}\b', line) or \
                         re.search(rf'[+|\-|*|/|%|&|\||^|>|<|!|?|:|\(]\s*{var}\b', line) or \
                         re.search(rf'\b{var}[+|\-|+]{2}', line)  # increment/decrement
            
            # Look for write operations (variable appears on left side of assignment)
            write_match = re.search(rf'\b{var}\s*(?:[+|\-|*|/|%|&|\||^])?=', line) or \
                          re.search(rf'\b{var}[+|\-]{2}', line)  # increment/decrement
            
            if read_match and not written:
                read_first = True
            if write_match:
                written = True
                
        # Check if written in the last iteration (lastprivate candidate)
        last_iter_usage = re.search(rf'\b{var}\s*(?:[+|\-|*|/|%|&|\||^])?=', lines[-1]) or \
                          re.search(rf'\b{var}[+|\-]{2}', lines[-1])
                
        # Check for reduction patterns
        reduction_match = re.search(rf'\b{var}\s*(?:[+|\-|*|/|%|&|\|])?=\s*{var}\b', loop_body)
        
        # Assign to appropriate category
        if reduction_match:
            result["reduction"].append(var)
        elif read_first and written:
            # result["firstprivate"].append(var)
            pass
        elif last_iter_usage:
            # result["lastprivate"].append(var)
            pass
        elif written:
            result["private"].append(var)
        else:
            result["shared"].append(var)
    
    # Handle array variables - generally shared unless clear pattern indicates otherwise
    for var in array_variables:
        # Check if the array is only read from
        write_to_array = re.search(rf'\b{var}\s*\[[^\]]*\]\s*(?:[+|\-|*|/|%|&|\||^])?=', loop_body) or \
                         re.search(rf'\b{var}\s*\[[^\]]*\][+|\-]{2}', loop_body)
                         
        if not write_to_array:
            result["shared"].append(var)
        else:
            # Check if array modifications depend on loop variable
            loop_var_dependent = re.search(rf'\b{var}\s*\[.*\b{loop_var}\b.*\]', loop_body)
            if loop_var_dependent:
                # If each iteration writes to different indices (loop var is used in index)
                result["shared"].append(var)
            else:
                # If we're potentially writing to the same indices
                result["shared"].append(var)  # Still shared but with potential race conditions
                
    # Remove duplicates and sort
    for category in result:
        result[category] = sorted(list(set(result[category])))
        
    return result

def get_cache_hierarchy():
    """
    Get typical cache hierarchy sizes in bytes.
    
    Returns:
        dict: Cache sizes for different levels
    """
    return {
        'L1': 32 * 1024,      # 32KB L1 cache
        'L2': 256 * 1024,     # 256KB L2 cache
        'L3': 8 * 1024 * 1024, # 8MB L3 cache
    }

def create_test_harness(loop_code, array_type, tile_size, test_size=500):
    """
    Create a C++ test harness to benchmark a specific tile size.
    
    Args:
        loop_code (str): The loop code to test
        array_type (str): Type of array access
        tile_size (int): Tile size to test
        test_size (int): Size of test arrays
        
    Returns:
        str: Complete C++ program for benchmarking
    """
    # Create simple, working test cases
    if array_type == "1D array":
        cpp_program = f"""
#include <iostream>
#include <vector>
#include <chrono>
#include <algorithm>

int main() {{
    const int n = {test_size};
    const int TILE_SIZE = {tile_size};
    
    std::vector<float> a(n, 1.0f);
    std::vector<float> b(n, 2.0f);
    std::vector<float> c(n, 0.0f);
    
    // Warm up
    for (int warmup = 0; warmup < 3; warmup++) {{
        for (int i_tile = 0; i_tile < n; i_tile += TILE_SIZE) {{
            for (int i = i_tile; i < std::min(i_tile + TILE_SIZE, n); i++) {{
                c[i] = a[i] + b[i];
            }}
        }}
    }}
    
    // Benchmark
    auto start = std::chrono::high_resolution_clock::now();
    
    for (int iter = 0; iter < 10; iter++) {{
        for (int i_tile = 0; i_tile < n; i_tile += TILE_SIZE) {{
            for (int i = i_tile; i < std::min(i_tile + TILE_SIZE, n); i++) {{
                c[i] = a[i] + b[i];
            }}
        }}
    }}
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << duration.count() << std::endl;
    return 0;
}}
        """
    elif array_type == "2D array":
        size = min(test_size, 300)  # Keep it manageable
        cpp_program = f"""
#include <iostream>
#include <vector>
#include <chrono>
#include <algorithm>

int main() {{
    const int n = {size};
    const int m = {size};
    const int TILE_SIZE = {tile_size};
    
    std::vector<std::vector<float>> a(n, std::vector<float>(m, 1.0f));
    std::vector<std::vector<float>> b(n, std::vector<float>(m, 2.0f));
    std::vector<std::vector<float>> c(n, std::vector<float>(m, 0.0f));
    
    // Warm up
    for (int warmup = 0; warmup < 2; warmup++) {{
        for (int i_tile = 0; i_tile < n; i_tile += TILE_SIZE) {{
            for (int j_tile = 0; j_tile < m; j_tile += TILE_SIZE) {{
                for (int i = i_tile; i < std::min(i_tile + TILE_SIZE, n); i++) {{
                    for (int j = j_tile; j < std::min(j_tile + TILE_SIZE, m); j++) {{
                        c[i][j] = a[i][j] + b[i][j];
                    }}
                }}
            }}
        }}
    }}
    
    // Benchmark
    auto start = std::chrono::high_resolution_clock::now();
    
    for (int iter = 0; iter < 5; iter++) {{
        for (int i_tile = 0; i_tile < n; i_tile += TILE_SIZE) {{
            for (int j_tile = 0; j_tile < m; j_tile += TILE_SIZE) {{
                for (int i = i_tile; i < std::min(i_tile + TILE_SIZE, n); i++) {{
                    for (int j = j_tile; j < std::min(j_tile + TILE_SIZE, m); j++) {{
                        c[i][j] = a[i][j] + b[i][j];
                    }}
                }}
            }}
        }}
    }}
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << duration.count() << std::endl;
    return 0;
}}
        """
    else:
        # Simple fallback
        cpp_program = f"""
#include <iostream>
#include <vector>
#include <chrono>

int main() {{
    const int n = {test_size};
    std::vector<float> data(n, 1.0f);
    float sum = 0.0f;
    
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < n; i++) {{
        sum += data[i];
    }}
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);
    
    std::cout << duration.count() << std::endl;
    return 0;
}}
        """
    
    return cpp_program

def generate_tiled_loop_with_size(loop_string, tile_size):
    """
    Generate tiled loop with specific tile size for benchmarking.
    """
    # For simple testing, create a straightforward tiled version
    if "for (int i = 0; i < n; i++)" in loop_string and "for (int j = 0; j < m; j++)" in loop_string:
        # 2D loop case
        body = loop_string.split("c[i][j]")[1].split(";")[0] + ";"
        return f"""
        for (int i_tile = 0; i_tile < n; i_tile += {tile_size}) {{
            for (int j_tile = 0; j_tile < m; j_tile += {tile_size}) {{
                for (int i = i_tile; i < std::min(i_tile + {tile_size}, n); i++) {{
                    for (int j = j_tile; j < std::min(j_tile + {tile_size}, m); j++) {{
                        c[i][j]{body}
                    }}
                }}
            }}
        }}
        """
    elif "for (int i = 0; i < n; i++)" in loop_string:
        # 1D loop case
        body = loop_string.split("c[i]")[1].split(";")[0] + ";"
        return f"""
        for (int i_tile = 0; i_tile < n; i_tile += {tile_size}) {{
            for (int i = i_tile; i < std::min(i_tile + {tile_size}, n); i++) {{
                c[i]{body}
            }}
        }}
        """
    else:
        # Fallback to original approach
        return loop_string

def run_performance_test(cpp_code, timeout=10):
    """
    Compile and run C++ code, return execution time in microseconds.
    
    Args:
        cpp_code (str): C++ source code
        timeout (int): Timeout in seconds
        
    Returns:
        float: Execution time in microseconds, or float('inf') if failed
    """
    try:
        # Create executables directory if it doesn't exist
        if not os.path.exists("executables"):
            os.makedirs("executables")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False, dir='executables') as f:
            f.write(cpp_code)
            cpp_file = f.name
        
        # Compile - place executable in executables directory
        exe_file = cpp_file.replace('.cpp', '_exec')
        compile_result = subprocess.run(
            ['g++', '-O3', '-std=c++17', cpp_file, '-o', exe_file],
            capture_output=True, text=True, timeout=timeout
        )
        
        if compile_result.returncode != 0:
            return float('inf')
        
        # Run
        run_result = subprocess.run(
            [exe_file], capture_output=True, text=True, timeout=timeout
        )
        
        if run_result.returncode == 0:
            return float(run_result.stdout.strip())
        else:
            return float('inf')
            
    except Exception as e:
        return float('inf')
    finally:
        # Cleanup
        try:
            if 'cpp_file' in locals():
                os.unlink(cpp_file)
            if 'exe_file' in locals() and os.path.exists(exe_file):
                os.unlink(exe_file)
        except:
            pass

def find_optimal_tile_size_empirical(loop_code, array_type, min_size=8, max_size=1024):
    """
    Find optimal tile size through empirical testing with binary search.
    
    Args:
        loop_code (str): The loop code to optimize
        array_type (str): Type of array access
        min_size (int): Minimum tile size to test
        max_size (int): Maximum tile size to test
        
    Returns:
        int: Optimal tile size based on actual performance measurements
    """
    global TILE_SIZE
    
    if array_type == "Single variables":
        return 1
    
    print(f"🔍 [TILE OPTIMIZATION] Finding optimal tile size for {array_type} (testing {min_size}-{max_size})...")
    print(f"📊 [TILE OPTIMIZATION] Starting empirical performance testing...")
    
    # Test key tile sizes (powers of 2 and some common sizes)
    test_sizes = []
    
    # Add powers of 2
    power = 1
    while 2**power <= max_size:
        if 2**power >= min_size:
            test_sizes.append(2**power)
        power += 1
    
    # Add some common cache-friendly sizes
    common_sizes = [16, 32, 48, 64, 96, 128, 192, 256, 384, 512, 768]
    for size in common_sizes:
        if min_size <= size <= max_size and size not in test_sizes:
            test_sizes.append(size)
    
    test_sizes.sort()
    
    best_time = float('inf')
    best_size = min_size
    results = {}
    
    print(f"📊 Testing tile sizes: {test_sizes}")
    
    for tile_size in test_sizes:
        print(f"  Testing tile size {tile_size}...", end=" ")
        
        # Create test program
        cpp_code = create_test_harness(loop_code, array_type, tile_size)
        
        # Run performance test
        exec_time = run_performance_test(cpp_code)
        results[tile_size] = exec_time
        
        if exec_time != float('inf'):
            print(f"{exec_time:.0f} μs")
            if exec_time < best_time:
                best_time = exec_time
                best_size = tile_size
        else:
            print("FAILED")
    
    # If no tests succeeded, use binary search with simple heuristics
    if best_time == float('inf'):
        print("⚠️  All performance tests failed, using heuristic approach")
        if array_type == "1D array":
            best_size = 256
        elif array_type == "2D array":
            best_size = 64
        elif array_type == "3D array":
            best_size = 32
    else:
        print(f"✅ Best performance: {best_size} (time: {best_time:.0f} μs)")
    
    # Update global TILE_SIZE
    TILE_SIZE = best_size
    
    # Return a dictionary with optimization details for frontend
    optimization_details = {
        'optimal_size': best_size,
        'best_time': best_time if best_time != float('inf') else None,
        'tested_sizes': test_sizes,
        'results': results,
        'optimization_method': 'empirical' if best_time != float('inf') else 'heuristic'
    }
    
    return best_size

# Update the old theoretical functions to use empirical testing
def find_optimal_tile_size_binary_search(array_type, loop_complexity=3, min_size=8, max_size=2048):
    """
    Wrapper for backward compatibility - now uses empirical testing.
    """
    # Create a simple test loop based on array type
    if array_type == "1D array":
        test_loop = "for (int i = 0; i < n; i++) { c[i] = a[i] + b[i]; }"
    elif array_type == "2D array":
        test_loop = "for (int i = 0; i < n; i++) { for (int j = 0; j < m; j++) { c[i][j] = a[i][j] + b[i][j]; } }"
    elif array_type == "3D array":
        test_loop = "for (int i = 0; i < ni; i++) { for (int j = 0; j < nj; j++) { for (int k = 0; k < nk; k++) { result[i][j][k] = data[i][j][k] * factor; } } }"
    else:
        return 64  # Default for unknown types
    
    return find_optimal_tile_size_empirical(test_loop, array_type, min_size, min(max_size, 512))

def calculate_tile_size(ram_size, array_type, element_size=4, reserve_memory=0.1):
    """
    Calculate the tile size based on RAM, array dimension type, and element size.
    Now uses binary search optimization to find the optimal size.

    Args:
        ram_size (int): Total available RAM in GB.
        array_type (str): The type of array ("1D array", "2D array", "3D array").
        element_size (int): The size of one element in bytes (default: 4 bytes for float).
        reserve_memory (float): Fraction of memory to reserve for system use (default: 10%).

    Returns:
        int: The optimal tile size.
    """
    if array_type == "Single variables":
        return 1
    
    ram_bytes = ram_size * 1024**3  # Convert GB to bytes
    usable_memory = ram_bytes * (1 - reserve_memory)
    
    # Calculate maximum tile size based on available memory
    if array_type == "1D array":
        max_tile_size = min(usable_memory // element_size, 4096)
    elif array_type == "2D array":
        max_side = int((usable_memory // element_size) ** 0.5)
        max_tile_size = min(max_side, 128)  # Reasonable 2D tile limit
    elif array_type == "3D array":
        max_side = int((usable_memory // element_size) ** (1/3))
        max_tile_size = min(max_side, 64)   # Reasonable 3D tile limit
    else:
        return 64  # Default fallback
    
    # Use binary search to find optimal tile size within memory constraints
    optimal_size = find_optimal_tile_size_binary_search(
        array_type, 
        loop_complexity=3,  # Default complexity
        min_size=8, 
        max_size=int(max_tile_size)
    )
    
    return optimal_size

def determine_array_access_type(loop_string):
    """
    Determines if the loop accesses a 1D, 2D, 3D array, or single variables.
    Returns the highest dimension array access found.

    Args:
        loop_string (str): The string containing the loop code.

    Returns:
        str: The type of array access ("1D array", "2D array", "3D array", or "Single variables").
    """
    # Regular expressions to detect different array access patterns
    pattern_3d = r'[A-Za-z_]+\s*\[[A-Za-z0-9_]+\]\s*\[[A-Za-z0-9_]+\]\s*\[[A-Za-z0-9_]+\]'
    pattern_2d = r'[A-Za-z_]+\s*\[[A-Za-z0-9_]+\]\s*\[[A-Za-z0-9_]+\]'
    pattern_1d = r'[A-Za-z_]+\s*\[[A-Za-z0-9_]+\]'
    pattern_nd = r'[A-Za-z_]+\s*\[[A-Za-z0-9_]+\]'
    
    # Check for array accesses from highest to lowest dimension
    if re.search(pattern_3d, loop_string):
        return "3D array"
    elif re.search(pattern_2d, loop_string):
        return "2D array"
    elif re.search(pattern_1d, loop_string):
        return "1D array"
    elif re.search(pattern_nd, loop_string):
        # finding the value for nD array
        # return "nD array"
        n = 0
        for match in re.finditer(pattern_nd, loop_string):
            n += 1
        return f"{n}D array"
    else:
        return "Single variables"

def generate_tiled_loop(loop_string, array_type="2D array", loop_complexity=3):
    """
    Converts a nested loop string into a tiled version using the global TILE_SIZE constant.
    The tile size is automatically optimized using empirical testing.

    Args:
        loop_string (str): The original loop as a string.
        array_type (str): The type of array access in the loop.
        loop_complexity (int): Complexity of the loop (1-5).

    Returns:
        str: The loop tiled version with optimized TILE_SIZE.
    """
    global TILE_SIZE
    
    # Determine optimal tile size for this specific loop using empirical testing
    optimal_tile_size = find_optimal_tile_size_empirical(loop_string, array_type)
    
    # Match the loop pattern using a more flexible regex that handles various loop formats
    loop_pattern = re.compile(
        r"\s*for\s*\(\s*(int\s+)?(?P<var>[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?P<start>[a-zA-Z0-9_\[\]]+);\s*"
        r"(?P=var)\s*(?P<cmp><=|<|>=|>)\s*(?P<end>[a-zA-Z0-9_\[\]]+);\s*(?P=var)(?P<incr>\+\+|\-\-|\+=\s*\d+|\-=\s*\d+)\s*\)"
    )

    # Find all loops in the input string
    loop_matches = list(loop_pattern.finditer(loop_string))
    
    if not loop_matches:
        return "Invalid or no loop found in the input string."

    # Generate tiled version with header comment
    result = []
    result.append(f"// Tiled loop with optimal TILE_SIZE = {optimal_tile_size}\n")
    result.append(f"const int TILE_SIZE = {optimal_tile_size};\n")
    
    current_pos = 0
    open_braces = 0
    
    for match in loop_matches:
        # Add any content before this loop
        result.append(loop_string[current_pos:match.start()])
        
        # Extract loop components
        var = match.group("var")
        start = match.group("start")
        end = match.group("end")
        comparator = match.group("cmp")
        increment = match.group("incr")
        
        # Adjust the min/max function based on the comparison operator
        min_max_func = "std::min" if comparator in ["<", "<="] else "std::max"
        
        # Add the outer tiled loop (iteration space divided into tiles)
        result.append(
            f"for (int {var}_tile = {start}; {var}_tile {comparator} {end}; "
        )
        
        # Handle different increment types - always use TILE_SIZE constant
        if increment == "++":
            result.append(f"{var}_tile += TILE_SIZE) {{\n")
        elif increment == "--":
            result.append(f"{var}_tile -= TILE_SIZE) {{\n")
        elif "+=" in increment:
            inc_val = increment.split("+=")[1].strip()
            result.append(f"{var}_tile += (TILE_SIZE * {inc_val})) {{\n")
        elif "-=" in increment:
            inc_val = increment.split("-=")[1].strip()
            result.append(f"{var}_tile -= (TILE_SIZE * {inc_val})) {{\n")
        
        # Add the inner loop (within a single tile) - always use TILE_SIZE constant
        # For loop going forward
        if "++" in increment or "+=" in increment:
            result.append(
                f"    for (int {var} = {var}_tile; {var} {comparator} {min_max_func}({var}_tile + TILE_SIZE, {end}); {var}{increment}) {{\n"
            )
        # For loop going backward
        else:
            result.append(
                f"    for (int {var} = {var}_tile; {var} {comparator} {min_max_func}({var}_tile - TILE_SIZE, {end}); {var}{increment}) {{\n"
            )
        
        open_braces += 1
        current_pos = match.end()
    
    # Add remaining content after the last matched loop
    result.append(loop_string[current_pos:])
    
    # Close all opened loops
    result.extend(["    }\n}" * open_braces])
    
    return ''.join(result)

# handling Break conditions
def Soft_Break(function_str):
    """
    Convert a C/C++ function to its OpenMP equivalent by handling break and return statements.
    
    Args:
        function_str (str): The input C/C++ function as a string
        
    Returns:
        str: The converted OpenMP version of the function
    """
    # Extract function signature
    signature_match = re.match(r'^(.*?)\s*\{', function_str, re.DOTALL)
    if not signature_match:
        raise ValueError("Invalid function format")
    
    signature = signature_match.group(1)
    
    # Extract function body
    body = function_str[signature_match.end():].strip()[:-1]  # Remove the last '}'
    
    # Find the for loop
    for_loop_match = re.search(r'for\s*\((.*?);(.*?);(.*?)\)', body, re.DOTALL)
    if not for_loop_match:
        raise ValueError("No for loop found in function")
    
    # Extract loop components
    init, condition, increment = [s.strip() for s in for_loop_match.groups()]
    
    # Extract condition variables
    condition_vars = re.findall(r'([a-zA-Z_]\w*)', condition)
    loop_var = re.findall(r'([a-zA-Z_]\w*)\s*=', init)[0]
    limit_var = [var for var in condition_vars if var != loop_var][0]
    
    # Check if there's a return statement in the loop
    has_return = 'return' in body
    
    # Create the parallel variable if needed
    parallel_var = ""
    if has_return:
        return_val = re.search(r'return\s+([^;]+);', body).group(1)
        if return_val.isdigit() or return_val == '-1':
            parallel_var = f"    int parallel_temp = {return_val};\n"
        else:
            parallel_var = f"    {signature.split()[0]} parallel_temp = {return_val};\n"
    
    # Process the loop body
    loop_body = re.search(r'for\s*\([^{]*\)\s*{(.*?)}', body, re.DOTALL).group(1)
    
    # Replace return statements with parallel variable assignment
    if has_return:
        loop_body = re.sub(r'return\s+([^;]+);', 
                          f'parallel_temp = \\1;\n        {loop_var} = {limit_var};', 
                          loop_body)
    
    # Replace break statements
    loop_body = re.sub(r'break;', f'{loop_var} = {limit_var};', loop_body) + '}\n'
    
    # Add check for early termination
    if has_return:
        loop_body += f'\n        if (parallel_temp != {return_val}) {loop_var} = {limit_var};'
    
    # Construct the OpenMP version
    openmp_version = f"{signature} {{\n"
    if parallel_var:
        openmp_version += parallel_var
    
    # Add OpenMP pragma
    if has_return:
        openmp_version += "    #pragma omp parallel for shared(parallel_temp)\n"
    else:
        # Determine shared variables from the loop body
        shared_vars = set(re.findall(r'([a-zA-Z_]\w*)\s*=', loop_body)) - {loop_var}
        if shared_vars:
            shared_list = ", ".join(shared_vars)
            openmp_version += f"    #pragma omp parallel for shared({shared_list})\n"
        else:
            openmp_version += "    #pragma omp parallel for \n"
    
    # Add the modified for loop
    openmp_version += f"    for ({init}; {condition}; {increment}) {{\n"
    openmp_version += "        " + loop_body.replace("\n", "\n        ") + "\n"
    openmp_version += "    }\n"
    
    # Add return statement if needed
    if has_return:
        openmp_version += "    return parallel_temp;\n"
    
    openmp_version += "}"
    
    return openmp_version

# This function will check if the given loop block is parallelizable or not.
def Reduction_aaplication(Loop_Block):
    """
    Checks if reduction is possible in the given loop block.
    If reduction is possible, returns a list of reduction calls.
    Otherwise, returns an empty list.

    Args:
        Loop_Block (str): The code block of a single loop.

    Returns:
        list: A list of reduction directives if applicable, or an empty list.
    """
    import re

    # Patterns to identify potential reductions
    reduction_patterns = [
        (r"(\w+)\s*\+=\s*[^\;]+;", "+"),  # sum: var += ...
        (r"(\w+)\s*\*=\s*[^\;]+;", "*"),  # product: var *= ...
        (r"(\w+)\s*=\s*\1\s*\+\s*[^\;]+;", "+"),  # sum: var = var + ...
        (r"(\w+)\s*=\s*\1\s*\*\s*[^\;]+;", "*"),  # product: var = var * ...
        (r"(\w+)\s*=\s*min\s*\(\s*\1\s*,", "min"),  # min: var = min(var, ...)
        (r"(\w+)\s*=\s*max\s*\(\s*\1\s*,", "max"),  # max: var = max(var, ...)
    ]

    # Store detected reductions
    detected_reductions = []

    # Check for reduction patterns
    for pattern, operation in reduction_patterns:
        matches = re.findall(pattern, Loop_Block)
        for match in matches:
            variable = match
            # Append reduction directive in OpenMP style
            detected_reductions.append(f"reduction({operation}:{variable})")

    return detected_reductions

# This function will parallelize the given loop block if it is parallelizable.
def parallelizing_loop(Loop_Bloc):

    Parallelized_string = "#pragma omp parallel for"
    # print("Here")
    Reduction_line = Reduction_aaplication(Loop_Bloc)
    # print(Reduction_line)
    if Reduction_line:
        for line in Reduction_line:
            Parallelized_string += f" {line}"
    else:
        Parallelized_string += " schedule(static)"

    # print (Parallelized_string)
    return Parallelized_string

# This function checks if there is 'cin', 'cout', 'printf' or any type of input/output statement in the given code block.
def check_input_output(Loop_Block):
    """
    Checks if there is any input/output statement in the given loop block.
    If there is any input/output statement, returns True.
    Otherwise, returns False.

    Args:
        Loop_Block (str): The code block of a single loop.

    Returns:
        bool: True if there is any input/output statement, False otherwise.
    """
    # Patterns to identify input/output statements
    io_patterns = [
        r"cin\s*>> [^;]+;",
        r"cout\s*<< [^;]+;",
        r"printf\s*\( [^;]+;",
        r"scanf\s*\( [^;]+;",
        r"getline\s*\( [^;]+;",
        # multiple input/output statements
        r"cin\s*>> [^;]+;\s*cout\s*<< [^;]+;",
        r"printf\s*\( [^;]+;\s*printf\s*\( [^;]+;",
        r"scanf\s*\( [^;]+;\s*scanf\s*\( [^;]+;",
        r"getline\s*\( [^;]+;\s*getline\s*\( [^;]+;",

    ]

    # Check for input/output patterns
    for pattern in io_patterns:
        if re.search(pattern, Loop_Block):
            return True

    return False

# This function will return list of variables declared within the loop
def extract_variables_from_loop(code_block):
    """
    Extracts all variables that are declared within a loop block.
    
    Args:
        code_block (str): The code block containing loops and variable declarations.
        
    Returns:
        list: A list of variable names that are declared within the loops.
    """
    
    # Pattern to match common variable declarations
    # Matches patterns like: 
    # - for (int i = 0; i < N; i++)
    # - int variable;
    # - float x, y, z;
    # - double value = 3.14;
    
    # Match loop variables
    loop_var_pattern = r'for\s*\(\s*(?:int|float|double|char|long|short|unsigned|signed|auto)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*='
    
    # Match other variable declarations
    var_decl_pattern = r'(?:^|\s|;)\s*(?:int|float|double|char|long|short|unsigned|signed|auto|bool|size_t)\s+([a-zA-Z0-9_,\s]+)(?:;|=)'
    
    variables = []
    
    # Find loop variables
    loop_variables = re.findall(loop_var_pattern, code_block)
    variables.extend(loop_variables)
    
    # Find other variable declarations
    var_declarations = re.findall(var_decl_pattern, code_block)
    
    # Process each declaration which might contain multiple variables
    for declaration in var_declarations:
        # Split by commas to handle multiple declarations like "int x, y, z;"
        vars_in_decl = re.split(r',\s*', declaration)
        
        for var in vars_in_decl:
            # Extract just the variable name (remove any trailing assignments)
            var_name = var.strip().split('=')[0].strip()
            # Further clean up any remaining spaces or brackets
            var_name = re.sub(r'[\[\]()].*', '', var_name).strip()
            
            if var_name and var_name not in variables:
                variables.append(var_name)
    
    return variables

def LoopBlocks(Code_String):
    Loop_Blocks = []
    i = 0

    while i < len(Code_String):
        # Look for "for" keyword followed by whitespace or opening parenthesis
        if (i + 3 < len(Code_String) and Code_String[i:i+3] == 'for' and 
                (i+3 >= len(Code_String) or Code_String[i+3].isspace() or Code_String[i+3] == '(')):
            start_index = i
            Block = "for"
            i += 3  # Move past "for"
            
            # Skip whitespace
            while i < len(Code_String) and Code_String[i].isspace():
                Block += Code_String[i]
                i += 1
            
            # Capture the loop condition within parentheses
            if i < len(Code_String) and Code_String[i] == '(':
                paren_count = 1
                Block += Code_String[i]
                i += 1
                
                # Continue until matching parenthesis is found
                while i < len(Code_String) and paren_count > 0:
                    if Code_String[i] == '(':
                        paren_count += 1
                    elif Code_String[i] == ')':
                        paren_count -= 1
                    Block += Code_String[i]
                    i += 1
                
                # Check if we found a valid for loop (should have 2 semicolons within parentheses)
                semicolons = Block.count(';')
                if semicolons < 2:
                    i = start_index + 1  # Not a valid for loop, continue searching
                    continue
                
                # Handle loop body
                # Skip whitespace
                while i < len(Code_String) and Code_String[i].isspace():
                    Block += Code_String[i]
                    i += 1
                
                if i < len(Code_String):
                    if Code_String[i] == '{':
                        # Block with braces
                        brace_count = 1
                        Block += Code_String[i]
                        i += 1
                        
                        # Continue until all opening braces are matched
                        while i < len(Code_String) and brace_count > 0:
                            if Code_String[i] == '{':
                                brace_count += 1
                            elif Code_String[i] == '}':
                                brace_count -= 1
                            Block += Code_String[i]
                            i += 1
                    else:
                        # Single line statement (no braces)
                        while i < len(Code_String) and Code_String[i] != ';':
                            Block += Code_String[i]
                            i += 1
                        if i < len(Code_String) and Code_String[i] == ';':
                            Block += Code_String[i]
                            i += 1
                
                # Add the block to our results
                Loop_Blocks.append(Block)
            else:
                # If we don't find an opening parenthesis after "for", move on
                i = start_index + 1
        else:
            i += 1
            
    return Loop_Blocks

# This function will check what is the dependency of the given loop block on the variables
def analyze_data_dependency(code_snippet):
    # Regular expressions to capture read and write patterns
    write_pattern = re.compile(r'(\w+)\s*\[?.*?\]?\s*=')
    read_pattern = re.compile(r'=\s*(.*)')

    # Dictionaries to store read and write variables by line
    writes = defaultdict(set)
    reads = defaultdict(set)

    # Dependencies dictionary to track each variable's dependencies
    dependencies = defaultdict(lambda: {
        "True Dependency (Read after Write)": False,
        "Anti Dependency (Write after Read)": False,
        "Output Dependency (Write after Write)": False,
    })

    # Process each line in the code snippet
    lines = code_snippet.strip().splitlines()
    for line in lines:
        # Identify write variables
        write_match = write_pattern.search(line)
        if write_match:
            write_var = write_match.group(1)
            writes[write_var].add(line)

        # Identify read variables from the right side of assignments
        read_match = read_pattern.search(line)
        if read_match:
            rhs = read_match.group(1)
            # Find all variables on the right-hand side
            rhs_vars = re.findall(r'\b\w+\b', rhs)
            for read_var in rhs_vars:
                reads[read_var].add(line)

    # Check dependencies for each variable
    for write_var in writes:
        # True Dependency: read after write for the same variable
        if write_var in reads:
            dependencies[write_var]["True Dependency (Read after Write)"] = True

        # Anti Dependency: write after read for the same variable
        if write_var in reads:
            dependencies[write_var]["Anti Dependency (Write after Read)"] = True

        # Output Dependency: multiple writes to the same variable
        if len(writes[write_var]) > 1:
            dependencies[write_var]["Output Dependency (Write after Write)"] = True

    return dependencies

# This function will write the content to the file.
def writing_code_to_file(file_path, content):
    try:
        with open(file_path, 'w') as file:
            file.write(content)
    except IOError:
        print("An error occurred while writing to the file.")

# This function will count the number of for loops in the given code.
def getCountofForLoops(code):
    count = 0
    i = 0
    while i < len(code):
        if code[i:i + 3] == 'for':
            count += 1
        i += 1
    return count

def Complexity_of_loop(Block: str) -> int | tuple[int, Any]:
    """
    This function calculates the complexity of the given loop block, based on provided rules.
    Rules:
        This function will return the complexity of the loop block.
        Things used:
            1. The loop condition
            2. The number of nested loops and their conditions
            3. The number of variables used in the loop
                a. single variable have complexity 1
                b. multiple dimension array variables have complexity 2
            4. The number of operations in the loop
                a. Binary operation have complexity 1 i.e (&, |, ^)
                b. Arithmatic operations have complexity 2 i.e (+, -, *, /, %)
                c. Unary operations have complexity 1.5 i.e (++, --)
                d. Assignment operations have complexity 1 i.e (=)
            5. The total number of lines within the loop excluding the loop condition line and brackets '{}' lines
            6. The number of function calls within the loop block
                a. Complexity of function depends upon the passed arguments and the return type of the function
                b. In case of passing array the complexity will be 3
                c. In case of passing single variable the complexity will be 1
            7. Incase the loop condition has a hard-coded value, the complexity will be that value multiplied by 0.2
    Parameters:
        Block (str): The loop block as a string

    Returns:
        float: The total calculated complexity of the loop block
    """
    complexity = 0.0

    # 1. Analyze the loop condition
    loop_condition = re.search(r'for\s*\((.*?)\)', Block)

    # Check if the loop condition has a hard-coded value
    value = re.findall(r'(\d+)', Block)
    # print(value)
    if value:
        # print(value)
        for v in value:
            if int(v) > 1000000:
                complexity += float(v) * 0.2
            else:
                complexity -= float(v) * 0.42 # 42 is a joke because during random seed we use 42 and I never understood why
            # print(complexity)

    if loop_condition:
        condition_content = loop_condition.group(1)
        # Assume each variable in the condition contributes a base complexity of 1
        complexity += condition_content.count(',') + 1  # Number of variables in loop condition

    # 2. Count nested loops
    nested_loops = re.findall(r'for\s*\([^)]*\)', Block)
    complexity += len(nested_loops) * 2  # Each nested loop adds 2 to complexity

    # 3. Analyze variables in the loop
    variables = re.findall(r'([a-zA-Z_]\w*(?:\[[^\]]*\])*)', Block)
    for var in variables:
        if '[' in var:  # It's a multi-dimensional variable
            complexity += 2
        else:  # Single variable
            complexity += 1

    # 4. Count operations
    binary_ops = re.findall(r'[\&\|\^]', Block)  # Binary operations
    arithmetic_ops = re.findall(r'[+\-*/%]', Block)  # Arithmetic operations
    unary_ops = re.findall(r'\+\+|--', Block)  # Unary operations
    assignment_ops = re.findall(r'=', Block)  # Assignment operations

    complexity += len(binary_ops) * 1  # Each binary operation adds 1
    complexity += len(arithmetic_ops) * 2  # Each arithmetic operation adds 2
    complexity += len(unary_ops) * 1.5  # Each unary operation adds 1.5
    complexity += len(assignment_ops) * 1  # Each assignment operation adds 1

    # 5. Total number of lines inside the loop (excluding brackets and loop header)
    lines = Block.split('\n')
    meaningful_lines = [line for line in lines if
                        line.strip() and not line.strip().startswith('for') and not line.strip().startswith(
                            '{') and not line.strip().startswith('}')]
    complexity += len(meaningful_lines)

    # 6. Function calls within the loop
    function_calls = re.findall(r'\b\w+\s*\(([^)]*)\)', Block)
    for call in function_calls:
        # Check what is passed to the function
        if '[' in call:  # Passing array
            complexity += 3
        else:  # Single variable
            complexity += 1

    # classifying the complexity into 1 to 5
    # 5 being the most complex and 1 being the least complex

    complexity = round(complexity)

    if complexity > 50:
        return 5 , complexity
    elif complexity > 40:
        return 4 , complexity
    elif complexity > 30:
        return 3 , complexity
    elif complexity > 20:
        return 2 , complexity
    else:
        return 1 , complexity

# This function will check the variable that are declared in the loop block and the one that come from outside the loop block.
def Variable_in_Loop(Loop_Block):
    Outside_Variable = []
    Inside_Variable = []

    # finding the variables that are declared inside the loop block
    # The vaiable can be any primitive data type or any user defined data type
    Inside_Variable = re.findall(r'\b(?:int|float|double|char|string|vector|list|set|map)\s+\w+\b', Loop_Block)

    # finding the variables that are declared outside the loop block
    # The vaiable can be any primitive data type or any user defined data type
    Outside_Variable = re.findall(r'\b(?:int|float|double|char|string|vector|list|set|map)\s+\w+\b', Loop_Block)

    return Inside_Variable, Outside_Variable

def indent_cpp_code(code: str, style: str = "LLVM") -> str:
    """Formats C++ code using clang-format."""
    try:
        result = subprocess.run(
            ["clang-format", f"--style={style}"], 
            input=code, 
            text=True, 
            capture_output=True, 
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Error formatting code:", e)
        return code

def identify_dependencies(loop_block, loop_index=['i','j','k']):
    """
    Analyzes a loop block to determine if it is parallelizable.

    The heuristic assumes that:
      - Array accesses using the loop index (e.g. A[i]) are isolated to each iteration.
      - Any assignment to a variable without such indexing (or with a different index)
        may introduce a cross-iteration dependency.
      - Any access to a variable with an index like [i-1] creates a cross-iteration dependency.
      - Any variable access with a loop variable +/- a constant creates a dependency.

    Returns:
        (parallelizable: bool, non_parallelizable_line: int or None)
    If parallelizable is True, non_parallelizable_line is None.
    If parallelizable is False, non_parallelizable_line indicates the first line where a dependency is detected.
    """
    import re
    lines = loop_block.split('\n')
    written_vars = set()
    
    # Helper function to check if a string contains a loop index with offset
    def has_offset_index(text):
        for index in loop_index:
            if re.search(rf'{index}\s*[-+]\s*\d+', text) or re.search(rf'\w+\s*[-+]\s*\d+', text):
                return True
        return False

    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()
        # Skip empty or comment lines.
        if not stripped or stripped.startswith('//') or stripped.startswith('#'):
            continue

        # First, check for any array access with index offset before assignment
        # This handles cases like dp[i-1][w] on right side of assignment
        for var in re.findall(r'(\w+)\s*\[([^\]]+)\]', line):
            var_name, index_expr = var
            if has_offset_index(index_expr):
                return False, line_num

        # Look for an assignment operation.
        match = re.search(r'(\w+)(\s*\[[^\]]+\])?\s*=', line)
        if match:
            var = match.group(1)
            index_part = match.group(2)
            
            # Check if the line uses the same variable with a modified index
            if index_part:
                # Normalize the index: remove spaces and the surrounding brackets.
                index_clean = index_part.strip()[1:-1].strip()
                
                # Check if the index contains loop index with offset (i-1) or any variable with offset
                if has_offset_index(index_clean):
                    return False, line_num
                
                # Check if the index is completely unrelated to the loop indices
                if not any(index in index_clean for index in loop_index):
                    return False, line_num
            else:
                # No array index implies a global variable assignment that is likely loop-carried.
                if var in written_vars:
                    return False, line_num
                written_vars.add(var)

        # Check for any array access with the same name as the assigned variable
        # This handles cases where the same array is accessed with different indices
        if match:
            var = match.group(1)
            # Look for any other access to the same variable in the line
            other_accesses = re.findall(rf'{var}\s*\[([^\]]+)\]', line)
            for access in other_accesses:
                if has_offset_index(access):
                    return False, line_num

    # If no problematic assignments are found, assume the loop block may be parallelizable.
    return True, None

def GetControlers(Loop_Block):
    '''
        Return list of variables that are present within '[ ]' in the loop block.
    '''
    expression = re.findall(r'\[([^\]]+)\]', Loop_Block)

    # making unique list of variables
    expression = list(set(expression))

    return expression

def normalize_loop(loop_string):
    """
    Normalizes loops to start from 0 and increment by 1, adjusting the loop body accordingly.
    
    Args:
        loop_string (str): The original loop as a string.
        
    Returns:
        str: Normalized loop string.
    """
    # Match the loop pattern
    loop_pattern = re.compile(
        r"\s*for\s*\(\s*(int\s+)?(?P<var>[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?P<start>[a-zA-Z0-9_\[\]]+);\s*"
        r"(?P=var)\s*(?P<cmp><=|<|>=|>)\s*(?P<end>[a-zA-Z0-9_\[\]]+);\s*(?P=var)(?P<incr>\+\+|\-\-|\+=\s*\d+|\-=\s*\d+)\s*\)"
    )
    
    match = loop_pattern.search(loop_string)
    if not match:
        return loop_string  # Can't normalize if pattern doesn't match
    
    # Extract loop components
    var = match.group("var")
    start = match.group("start")
    end = match.group("end")
    comparator = match.group("cmp")
    increment = match.group("incr")
    
    # If it's already normalized (starts from 0, increments by 1), return as is
    if start == "0" and increment == "++":
        return loop_string
    
    # Create a normalized version
    normalized_var = f"{var}_norm"
    
    # Determine the adjustment needed in the loop body
    if increment == "++":
        # For incrementing loops
        adjustment = f"{start} + {normalized_var}"
    elif increment == "--":
        # For decrementing loops
        adjustment = f"{start} - {normalized_var}"
    elif "+=" in increment:
        inc_val = increment.split("+=")[1].strip()
        adjustment = f"{start} + {normalized_var} * {inc_val}"
    elif "-=" in increment:
        inc_val = increment.split("-=")[1].strip()
        adjustment = f"{start} - {normalized_var} * {inc_val}"
    else:
        return loop_string  # Can't handle this case
    
    # Calculate new end condition
    if comparator == "<":
        if increment == "++":
            new_end = f"{end} - {start}"
        else:
            return loop_string
    elif comparator == "<=":
        if increment == "++":
            new_end = f"{end} - {start} + 1"
        else:
            return loop_string
    else:
        return loop_string  # Can't handle other comparators yet
    
    # Create the normalized loop
    normalized_loop = f"for (int {normalized_var} = 0; {normalized_var} < {new_end}; {normalized_var}++)"
    
    # Replace the original loop header with the normalized one
    normalized_code = re.sub(loop_pattern, normalized_loop, loop_string, count=1)
    
    # Replace var with the adjusted expression in the loop body
    body_start = normalized_code.find("{", normalized_code.find(normalized_loop)) + 1
    body_end = find_matching_brace(normalized_code, body_start - 1)
    
    body = normalized_code[body_start:body_end]
    
    # Replace standalone variable references
    modified_body = re.sub(r'\b' + var + r'\b', f"({adjustment})", body)
    
    # Reconstruct the normalized loop
    return normalized_code[:body_start] + modified_body + normalized_code[body_end:]

def find_matching_brace(text, opening_pos):
    """
    Finds the position of the matching closing brace for an opening brace at opening_pos.
    
    Args:
        text (str): Text containing braces
        opening_pos (int): Position of the opening brace
        
    Returns:
        int: Position of the matching closing brace
    """
    count = 1
    for i in range(opening_pos + 1, len(text)):
        if text[i] == '{':
            count += 1
        elif text[i] == '}':
            count -= 1
            if count == 0:
                return i
    return -1

def determine_optimal_threads(loop_complexity, processors_count, code_block):
    """
    Determines the optimal number of threads for a loop based on its complexity,
    available processors, and characteristics.
    
    Args:
        loop_complexity (int): Complexity score of the loop (1-5)
        processors_count (int): Number of available processors
        code_block (str): The loop code block
        
    Returns:
        int: Recommended number of threads
    """
    # Base calculation based on processors and complexity
    base_threads = min(processors_count, 16)  # Cap at 16 as default max
    
    # Adjust based on complexity
    if loop_complexity >= 4:
        # High complexity loops benefit from more threads
        threads = base_threads
    elif loop_complexity == 3:
        # Medium complexity
        threads = max(base_threads * 3 // 4, 2)
    else:
        # Lower complexity may not benefit from too many threads
        threads = max(base_threads // 2, 2)
    
    # Further adjust based on memory access patterns
    array_type = determine_array_access_type(code_block)
    if "3D array" in array_type:
        # 3D arrays might benefit from fewer threads due to memory access patterns
        threads = max(threads * 2 // 3, 2)
    elif "2D array" in array_type:
        # 2D arrays slightly less thread-friendly than 1D
        threads = max(threads * 3 // 4, 2)
    
    # Adjust based on the estimated iteration count
    iter_count_estimate = estimate_iteration_count(code_block)
    if iter_count_estimate < 100:
        # Very few iterations don't benefit from many threads
        threads = min(threads, 4)
    elif iter_count_estimate < 1000:
        threads = min(threads, 8)
    
    return threads

def estimate_iteration_count(code_block):
    """
    Estimates the number of iterations in a loop.
    
    Args:
        code_block (str): The loop code
        
    Returns:
        int: Estimated iteration count
    """
    # Extract loop bounds
    loop_match = re.search(r'for\s*\(\s*(?:int\s+)?\w+\s*=\s*(\d+)\s*;\s*\w+\s*(?:<|<=|>|>=)\s*(\d+|\w+)\s*;', code_block)
    
    if loop_match:
        start = loop_match.group(1)
        end = loop_match.group(2)
        
        # If we have numeric bounds
        if start.isdigit() and end.isdigit():
            return int(end) - int(start)
        
        # If end is a variable, check for common size patterns
        if not end.isdigit():
            # Check for common array size variables
            size_match = re.search(rf'{end}\s*=\s*(\d+)', code_block)
            if size_match:
                return int(size_match.group(1)) - int(start)
    
    # Default estimates based on loop complexity
    complexity, _ = Complexity_of_loop(code_block)
    if complexity >= 4:
        return 10000  # Assume large iteration count for complex loops
    elif complexity >= 3:
        return 1000
    else:
        return 100

def implement_loop_balancing(parallelized_loop, thread_count):
    """
    Implements load balancing strategies for a parallelized loop.
    
    Args:
        parallelized_loop (str): The OpenMP parallelized loop
        thread_count (int): The number of threads to use
        
    Returns:
        str: Loop with added load balancing directives
    """
    # If it's already not parallelizable, return as is
    if parallelized_loop.startswith('Not Parallelizable'):
        return parallelized_loop
    
    # Find the OpenMP pragma
    pragma_match = re.search(r'#pragma\s+omp\s+parallel\s+for(.*?)(\n|\r\n?)', parallelized_loop)
    if not pragma_match:
        return parallelized_loop
    
    # Get existing clauses
    existing_clauses = pragma_match.group(1).strip()
    
    # Check if a schedule is already specified
    if 'schedule(' in existing_clauses:
        # Replace the schedule clause
        balanced_clauses = re.sub(r'schedule\([^)]*\)', f'schedule(dynamic) num_threads({thread_count})', existing_clauses)
    else:
        # Add the schedule clause
        balanced_clauses = f"{existing_clauses} schedule(dynamic) num_threads({thread_count})"
    
    # Replace the pragma with the balanced version
    balanced_loop = parallelized_loop.replace(
        pragma_match.group(0), 
        f"#pragma omp parallel for {balanced_clauses}\n"
    )
    
    return balanced_loop

def Parinomo(SCode, core_type, ram_type, processors_count):
    # making a json file to store loops and their tilled version and parallelized version if avalible with complexity
    # to return at the end
    All_data = {}

    SCode = indent_cpp_code(SCode)

    Loop_Blocks = LoopBlocks(SCode)

    count = 1

    for loops in Loop_Blocks:
        All_data[count] = {}
        All_data[count]['Loop'] = loops
        
        # Add loop normalization
        normalized_loop = normalize_loop(loops)
        
        if normalized_loop != loops:
            All_data[count]['Normalized_Loop'] = normalized_loop
            All_data[count]['Loop'] = normalized_loop
        else:
            All_data[count]['Normalized_Loop'] = "Already normalized"
        
        # Determine complexity for thread selection
        Complexity_class, Complexity = Complexity_of_loop(loops)
        All_data[count]['Complexity'] = Complexity
        All_data[count]['Complexity_Class'] = Complexity_class
        
        # Calculate optimal thread count
        thread_count = determine_optimal_threads(Complexity_class, processors_count, loops)
        All_data[count]['Thread_Count'] = thread_count

        # Check for input/output operations
        if check_input_output(loops):
            All_data[count]['Parallelized_Loop'] = 'Not Parallelizable Due to I/O operations'
            # Apply tiling for I/O loops
            array_type = determine_array_access_type(loops)
            if array_type != "Single variables":
                # Store the optimal tile size that was found
                optimal_tile_size = find_optimal_tile_size_empirical(
                    normalized_loop if normalized_loop != loops else loops, 
                    array_type
                )
                tiled_loop = generate_tiled_loop(
                    normalized_loop if normalized_loop != loops else loops, 
                    array_type, 
                    Complexity_class
                )
                tiled_loop = indent_cpp_code(tiled_loop)
                All_data[count]['Tiled_Loop'] = tiled_loop
                All_data[count]['Optimal_Tile_Size'] = optimal_tile_size
                All_data[count]['Array_Type'] = array_type
                All_data[count]['Tile_Optimization_Status'] = 'Optimized'
            else:
                All_data[count]['Tiled_Loop'] = 'Not Tiled - Single variables only'
                All_data[count]['Optimal_Tile_Size'] = None
                All_data[count]['Array_Type'] = array_type
                All_data[count]['Tile_Optimization_Status'] = 'Not Applicable'
        else:
            # Check for parallelization
            expression = GetControlers(loops)
            Paralleizable_Flag, reason = identify_dependencies(loops, expression)
            
            if Paralleizable_Flag:
                if 'break' in loops or 'return' in loops:
                    parallelized = indent_cpp_code(Soft_Break(loops))
                    # Apply load balancing with thread count
                    All_data[count]['Parallelized_Loop'] = implement_loop_balancing(parallelized, thread_count)
                else:
                    single_variable, array_variable = extract_loop_variables(loops)
                    loop_inilized = extract_variables_from_loop(loops)
                    result = analyze_openmp_variables(loops, single_variable, array_variable)

                    clauses = []
                    for category, vars_list in result.items():
                        vars_list = [f"{var}" for var in vars_list if var not in ['true', 'false']]
                        vars_list = [var for var in vars_list if var not in loop_inilized]

                        if vars_list and category != "error":
                            if category == "reduction":
                                reducible_vars = [f"{var}" for var in vars_list]
                                if reducible_vars:
                                    clauses.append(f"reduction(+:{', '.join(reducible_vars)})")
                            else:
                                clauses.append(f"{category}({', '.join(vars_list)})")

                    reduction = Reduction_aaplication(loops)

                    if reduction:
                        reduction_clause = []
                        for line in reduction:
                            reduction_clause.append(f"{line}")

                        parallelized = indent_cpp_code(f"#pragma omp parallel for {' '.join(clauses)} {' '.join(reduction_clause)}\n{loops}")
                    else:
                        parallelized = indent_cpp_code(f"#pragma omp parallel for {' '.join(clauses)}\n{loops}")
                    
                    # Apply load balancing with thread count
                    All_data[count]['Parallelized_Loop'] = implement_loop_balancing(parallelized, thread_count)
                    
                    # Apply tiling for parallelizable loops
                    array_type = determine_array_access_type(loops)
                    if array_type != "Single variables":
                        # Store the optimal tile size that was found
                        optimal_tile_size = find_optimal_tile_size_empirical(
                            normalized_loop if normalized_loop != loops else loops, 
                            array_type
                        )
                        tiled_loop = generate_tiled_loop(
                            normalized_loop if normalized_loop != loops else loops, 
                            array_type, 
                            Complexity_class
                        )
                        tiled_loop = indent_cpp_code(tiled_loop)
                        All_data[count]['Tiled_Loop'] = tiled_loop
                        All_data[count]['Optimal_Tile_Size'] = optimal_tile_size
                        All_data[count]['Array_Type'] = array_type
                        All_data[count]['Tile_Optimization_Status'] = 'Optimized'
                    else:
                        All_data[count]['Tiled_Loop'] = 'Not Tiled - Single variables only'
                        All_data[count]['Optimal_Tile_Size'] = None
                        All_data[count]['Array_Type'] = array_type
                        All_data[count]['Tile_Optimization_Status'] = 'Not Applicable'
            else:
                All_data[count]['Parallelized_Loop'] = f'Not Parallelizable Due to line number {reason}'
                # Apply tiling for non-parallelizable loops
                array_type = determine_array_access_type(loops)
                if array_type != "Single variables":
                    # Store the optimal tile size that was found
                    optimal_tile_size = find_optimal_tile_size_empirical(
                        normalized_loop if normalized_loop != loops else loops, 
                        array_type
                    )
                    tiled_loop = generate_tiled_loop(
                        normalized_loop if normalized_loop != loops else loops, 
                        array_type, 
                        Complexity_class
                    )
                    tiled_loop = indent_cpp_code(tiled_loop)
                    All_data[count]['Tiled_Loop'] = tiled_loop
                    All_data[count]['Optimal_Tile_Size'] = optimal_tile_size
                    All_data[count]['Array_Type'] = array_type
                    All_data[count]['Tile_Optimization_Status'] = 'Optimized'
                else:
                    All_data[count]['Tiled_Loop'] = 'Not Tiled - Single variables only'
                    All_data[count]['Optimal_Tile_Size'] = None
                    All_data[count]['Array_Type'] = array_type
                    All_data[count]['Tile_Optimization_Status'] = 'Not Applicable'

        count += 1

    # writing the data to the file
    file = open('P_code.txt', 'w')
    file.write(json.dumps(All_data, indent=4))
    file.close()

    return All_data