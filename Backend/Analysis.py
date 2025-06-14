import os
import subprocess
import csv
import re
import glob
import pandas as pd
from Parinomo import indent_cpp_code, LoopBlocks
from cleanup_executables import clean_all


def get_Insights(parallel, cpp_file, input_dir, num_runs=1):
    Files = []
    # print(f"Getting Insights for {input_dir} with {num_runs} runs per file")
    
    # Create executables directory if it doesn't exist
    if not os.path.exists("executables"):
        os.makedirs("executables")
        print("Created 'executables' directory for output files")
    
    # Place executable in the dedicated folder
    executable = "./executables/output_file"
    
    if not os.path.exists("Results"):
        os.makedirs("Results")
    if parallel == False:
        output_csv = "Results/ResultsSerial.csv"
    else:
        output_csv = "Results/ResultsParallel.csv"
    
    # Compile C++ Code
    if parallel == False:
        compile_command = f"g++ {cpp_file} -o {executable} -O2"
    else:
        compile_command = f"g++ {cpp_file} -o {executable} -O2 -fopenmp"
    
    compilation = subprocess.run(compile_command, shell=True, capture_output=True, text=True)
    if compilation.returncode != 0:
        print("Compilation failed:", compilation.stderr)
        # Clean up executable file if compilation failed
        if os.path.exists(executable):
            os.remove(executable)
        exit(1)
    else:
        print(f"Compilation successful. Executable created at: {executable}")
    
    # CSV Headers
    csv_header = [
        "Input File", 
        "Instruction References (I refs)", 
        "User Time (s)", 
        "System Time (s)", 
        "CPU Usage (%)", 
        "Elapsed Time (s)", 
        "Max RSS (KB)", 
        "Major Page Faults", 
        "Minor Page Faults", 
        "Voluntary Context Switches", 
        "Involuntary Context Switches", 
        "File System Inputs", 
        "File System Outputs"
    ]
    
    results = []
    
    # Check if input directory exists
    if not os.path.exists(input_dir):
        print(f"Warning: Input directory '{input_dir}' does not exist. Creating empty results.")
        # Return empty DataFrame with proper structure
        empty_df = pd.DataFrame(columns=csv_header)
        empty_df.to_csv(output_csv, index=False)
        return empty_df
    
    # Process each input file
    file_being_parsed = 0
    for file in sorted(os.listdir(input_dir)):

        # Skip non-txt files
        if not file.endswith(".txt"):
            continue
            
        # Try to extract number from filename (expecting format like "input_1.txt")
        try:
            File_name = file.split(".")[0]
            if "_" in File_name:
                File_name = File_name.split("_")[1]
                File_name = int(File_name)
            else:
                # If no underscore, try to extract number from filename
                numbers = re.findall(r'\d+', File_name)
                File_name = int(numbers[0]) if numbers else file_being_parsed + 1
        except (IndexError, ValueError) as e:
            print(f"Warning: Could not parse filename '{file}', using sequential number. Error: {e}")
            File_name = file_being_parsed + 1
        
        file_being_parsed += 1
        input_path = os.path.join(input_dir, file)
        Files.append(file)
        print(f"Processing file: {file} ({num_runs} runs)")
        
        # Initialize storage for multiple runs
        run_metrics = {
            "Instruction References (I refs)": [],
            "User Time (s)": [],
            "System Time (s)": [],
            "CPU Usage (%)": [],
            "Elapsed Time (s)": [],
            "Max RSS (KB)": [],
            "Major Page Faults": [],
            "Minor Page Faults": [],
            "Voluntary Context Switches": [],
            "Involuntary Context Switches": [],
            "File System Inputs": [],
            "File System Outputs": []
        }
        
        # Run multiple times
        for run in range(num_runs):
            print(f"  Run {run+1}/{num_runs}")
            command = f"/usr/bin/time -v valgrind --tool=callgrind {executable} < '{input_path}'"
            
            process = subprocess.run(command, shell=True, capture_output=True, text=True)
            stdout, stderr = process.stdout, process.stderr
            
            # Extract Callgrind instructions (I refs)
            instruction_refs = re.search(r"I\s+refs:\s+([\d,]+)", stdout)
            run_metrics["Instruction References (I refs)"].append(
                int(instruction_refs.group(1).replace(",", "")) if instruction_refs else 0
            )
            
            # Extract time and memory stats from stderr
            metric_patterns = {
                "User Time (s)": r"User time \(seconds\):\s+([\d.]+)",
                "System Time (s)": r"System time \(seconds\):\s+([\d.]+)",
                "CPU Usage (%)": r"Percent of CPU this job got:\s+([\d]+)%",
                "Elapsed Time (s)": r"Elapsed \(wall clock\) time.*?:\s+([\d:.]+)",
                "Max RSS (KB)": r"Maximum resident set size \(kbytes\):\s+(\d+)",
                "Major Page Faults": r"Major \(requiring I/O\) page faults:\s+(\d+)",
                "Minor Page Faults": r"Minor \(reclaiming a frame\) page faults:\s+(\d+)",
                "Voluntary Context Switches": r"Voluntary context switches:\s+(\d+)",
                "Involuntary Context Switches": r"Involuntary context switches:\s+(\d+)",
                "File System Inputs": r"File system inputs:\s+(\d+)",
                "File System Outputs": r"File system outputs:\s+(\d+)"
            }
            
            for metric, pattern in metric_patterns.items():
                match = re.search(pattern, stderr)
                if match:
                    # Convert time format (mm:ss.ms) to seconds if needed
                    if metric == "Elapsed Time (s)" and ":" in match.group(1):
                        time_parts = match.group(1).split(':')
                        if len(time_parts) == 2:  # mm:ss
                            value = float(time_parts[0]) * 60 + float(time_parts[1])
                        elif len(time_parts) == 3:  # hh:mm:ss
                            value = float(time_parts[0]) * 3600 + float(time_parts[1]) * 60 + float(time_parts[2])
                        else:
                            value = float(match.group(1))
                        # if parallel == 1 and file_being_parsed > 5 :
                        #     value *= 0.5
                    else:
                        value = float(match.group(1))
                        # if parallel == 1 and file_being_parsed > 5 :
                        #     value *= 0.5
                    run_metrics[metric].append(value)
                else:
                    run_metrics[metric].append(0)
            
        
        # changing file name key to File_name 
        run_metrics["Input File"] = File_name
        
        # Calculate averages
        avg_results = [file]
        for metric in csv_header[1:]:  # Skip "Input File"
            metric_values = run_metrics[metric]
            avg_value = sum(metric_values) / len(metric_values) if metric_values else 0
            
            # Format averages properly
            if metric == "Instruction References (I refs)" or "Context Switches" in metric or "Faults" in metric or "Inputs" in metric or "Outputs" in metric or "RSS" in metric:
                avg_results.append(int(avg_value))
            else:
                avg_results.append(round(avg_value, 2))
            
        # Add to results
        results.append(avg_results)
        print(f"Completed processing {file} (averaged over {num_runs} runs)")
    
    # Clean up executable after all runs
    try:
        if os.path.exists(executable):
            os.remove(executable)
            print(f"Cleaned up executable: {executable}")
    except Exception as e:
        print(f"Warning: Could not clean up executable {executable}: {e}")
    
    # Write results to CSV
    df = pd.DataFrame(results, columns=csv_header)
    df.to_csv(output_csv, index=False)
    print(f"Results saved to {output_csv}")
    
    return df

def detect_input_type(code):
    # Regex patterns for loop structures
    loop_pattern = re.compile(r'\b(for|while|do)\b[^{]*{')
    
    # Regex patterns for input types
    one_d_array = re.compile(r'\bcin\s*>>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[\s*[a-zA-Z0-9_]+\s*\]')
    two_d_array = re.compile(r'\bcin\s*>>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\[\s*[a-zA-Z0-9_]+\s*\]\s*\[\s*[a-zA-Z0-9_]+\s*\]')
    graph = re.compile(r'\bcin\s*>>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*>>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*;')
    weighted_graph = re.compile(r'\bcin\s*>>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*>>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*>>\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*;')
    
    # Find all loops
    loop_blocks = loop_pattern.findall(code)
    
    # Checking inside loop bodies
    for match in re.finditer(loop_pattern, code):
        loop_body_start = match.end()
        loop_body = code[loop_body_start:]
        
        # Find first closing brace to extract only loop content
        brace_count = 1
        for i, char in enumerate(loop_body):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    loop_body = loop_body[:i]
                    break
        
        # Check input type 
        if re.search(two_d_array, loop_body):
            return "2 D Array"
        elif re.search(one_d_array, loop_body):
            return "1 D Array"
        elif re.search(weighted_graph, loop_body):
            return "Weighted Graph"
        elif re.search(graph, loop_body):
            return "Graph"
    
    return "Unknown"

def Calling_for_analysis(Code,Type):

    # print("Indent Code")
    Code = indent_cpp_code(Code)
   
    # saving the Code string in a cpp file
    with open("Code.cpp", "w") as file:
        file.write(Code)

    # print("Splitting")
    Loops = LoopBlocks(Code)

    # finding the input type where will be cin statements
    Loop_found = ''
    Loop_found = detect_input_type(Code)
    
    print("Input type = ", Loop_found)
    
    # Check if input directory exists
    input_path = "Inputs/" + Loop_found
    if not os.path.exists(input_path):
        print(f"Warning: Input directory '{input_path}' does not exist.")
        # Create a default input directory or use a fallback
        fallback_dirs = ["Inputs/1 D Array", "Inputs/2 D Array", "Inputs/Graph", "Inputs/Weighted Graph"]
        input_path = None
        for fallback in fallback_dirs:
            if os.path.exists(fallback):
                input_path = fallback
                print(f"Using fallback directory: {fallback}")
                break
        
        if input_path is None:
            print("No valid input directories found. Creating empty results.")
            # Return empty DataFrame
            return pd.DataFrame()
    else:
        input_path = "Inputs/" + Loop_found

    # getting the insights
    try:
        df = get_Insights(Type, "Code.cpp", input_path)
    except Exception as e:
        print(f"Error in get_Insights: {e}")
        # Return empty DataFrame on error
        df = pd.DataFrame()

    clean_all()

    return df