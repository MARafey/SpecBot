import React, { useState, useEffect } from "react";
import Navbar from "./NavBar";
import Footer from "./Footer";
import { useLocation } from "react-router-dom";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import "./ParallelCodePage.css";
import { FaArrowRight } from "react-icons/fa";
import Swal from "sweetalert2";
import { useNavigate } from "react-router-dom";

const complexityColors = {
  1: "complexity-1",
  2: "complexity-2",
  3: "complexity-3",
  4: "complexity-4",
  5: "complexity-5",
};

const ParallelCodePage = ({ user }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const parallelizedCode = location.state?.parallelizedCode || "{}";
  const initialCodeInput = location.state?.codeInput || "{}";

  let extractedData = {};
  try {
    extractedData = JSON.parse(parallelizedCode);
  } catch (error) {
    console.error("Error parsing JSON:", error);
  }

  const [codeInput, setCodeInput] = useState(initialCodeInput);
  const [sortByDifference, setSortByDifference] = useState(false);
  const [filter, setFilter] = useState("all");
  const [sortByComplexity, setSortByComplexity] = useState(false);
  const [loops, setLoops] = useState(Object.values(extractedData));

  useEffect(() => {
    // console.log("Updated codeInput:", codeInput);
  }, [codeInput]);

  if (sortByDifference) {
    loops.sort((a, b) => {
      const diffA = Math.abs(
        (a.Parallelized_Loop?.length || 0) - (a.Tiled_Loop?.length || 0)
      );
      const diffB = Math.abs(
        (b.Parallelized_Loop?.length || 0) - (b.Tiled_Loop?.length || 0)
      );
      return diffB - diffA;
    });
  }

  if (sortByComplexity) {
    loops.sort((a, b) => {
      return (b.Complexity_Class || 0) - (a.Complexity_Class || 0);
    });
  }

  const replaceLoop = (loopObj, selectedOptimization = null) => {
    setCodeInput((prevCode) => {
      const originalLoop = loopObj.Loop;
      const parallelizedLoop = loopObj.Parallelized_Loop;
      const tiledLoop = loopObj.Tiled_Loop;

      // Check if both optimizations are available
      const hasParallel = parallelizedLoop && 
                         !parallelizedLoop.includes("Not Parallelizable") && 
                         parallelizedLoop !== "Not Parallelized";
      const hasTiled = tiledLoop && !tiledLoop.includes("Not Tiled");

      // If user hasn't selected and both options are available, show choice dialog
      if (!selectedOptimization && hasParallel && hasTiled) {
        Swal.fire({
          title: "Choose Optimization",
          text: "Both parallelized and tiled versions are available. Which would you prefer?",
          icon: "question",
          showCancelButton: true,
          confirmButtonText: "Use Parallelized",
          cancelButtonText: "Use Tiled",
          customClass: {
            actions: 'swal-actions-custom'
          },
          showCloseButton: true,
          html: `
            <div class="optimization-choice">
              <p>Both optimizations are available:</p>
              <div class="choice-details">
                <div class="choice-option">
                  <strong>🔄 Parallelized Version:</strong>
                  <p>Uses OpenMP directives for parallel execution across multiple threads</p>
                  <small>Recommended threads: ${loopObj.Thread_Count || 'N/A'}</small>
                </div>
                <div class="choice-option">
                  <strong>🧱 Tiled Version:</strong>
                  <p>Optimizes memory access patterns through loop tiling</p>
                  <small>Better cache performance and memory locality</small>
                </div>
              </div>
            </div>
          `
        }).then((result) => {
          if (result.isConfirmed) {
            // User chose parallelized
            replaceLoop(loopObj, 'parallel');
          } else if (result.dismiss === Swal.DismissReason.cancel) {
            // User chose tiled
            replaceLoop(loopObj, 'tiled');
          }
          // If dismissed with close button, do nothing
        });
        return prevCode;
      }

      // Determine which version to use
      let replacementLoop;
      let optimizationType;

      if (selectedOptimization === 'parallel' && hasParallel) {
        replacementLoop = parallelizedLoop;
        optimizationType = "Parallelized";
      } else if (selectedOptimization === 'tiled' && hasTiled) {
        replacementLoop = tiledLoop;
        optimizationType = "Tiled";
      } else if (hasParallel) {
        replacementLoop = parallelizedLoop;
        optimizationType = "Parallelized";
      } else if (hasTiled) {
        replacementLoop = tiledLoop;
        optimizationType = "Tiled";
      } else {
        // No valid replacement exists
        Swal.fire({
          title: "No Optimized Version!",
          text: "This loop doesn't have a parallelized or tiled version",
          icon: "warning",
          confirmButtonText: "OK",
        });
        return prevCode;
      }

      const normalize = (code) =>
        code
          .replace(/\/\/.*|\/\*[\s\S]*?\*\//g, "") // Remove comments
          .replace(/([{}();=<>+\-*/%&|\[\]])/g, " $1 ") // Add spaces around symbols
          .replace(/\s+/g, " ") // Remove extra spaces
          .trim();

      const createPattern = (str) => {
        return normalize(str)
          .split(" ")
          .filter((s) => s)
          .map((s) => s.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&"))
          .join("\\s*"); // Create a regex pattern with flexible spaces
      };

      const checkRegex = new RegExp(createPattern(originalLoop), "g");

      if (checkRegex.test(normalize(prevCode))) {
        // console.log("✅ Original Loop Found in Code");

        const newCode = prevCode.replace(checkRegex, (match) => {
          return replacementLoop; // Replace with chosen optimized loop
        });

        // Only show success message if not in bulk mode
        if (!selectedOptimization || (selectedOptimization !== 'parallel' && selectedOptimization !== 'tiled')) {
          Swal.fire({
            title: "Loop Replaced!",
            text: `${optimizationType} version inserted successfully 🎉`,
            icon: "success",
            confirmButtonText: "OK",
          });
        }

        // Remove the loop from the list after replacement
        setLoops((prevLoops) => prevLoops.filter((loop) => loop !== loopObj));

        // save the new code to session storage
        sessionStorage["ParallelCode"] = newCode;

        return newCode;
      }

      // Only show error message if not in bulk mode
      if (!selectedOptimization || (selectedOptimization !== 'parallel' && selectedOptimization !== 'tiled')) {
        Swal.fire({
          title: "Loop Not Found!",
          text: "Original loop not found in current code",
          icon: "error",
          confirmButtonText: "OK",
        });
      }

      return prevCode;
    });
  };

  const showTileOptimizationDetails = (loopObj) => {
    const tileSize = loopObj.Optimal_Tile_Size;
    const arrayType = loopObj.Array_Type;
    const status = loopObj.Tile_Optimization_Status;
    
    let detailsHtml = `
      <div class="tile-optimization-details">
        <h3>🧱 Tile Size Optimization Results</h3>
        <div class="optimization-summary">
          <div class="detail-row">
            <strong>Array Type:</strong> <span class="array-type-detail">${arrayType}</span>
          </div>
          <div class="detail-row">
            <strong>Optimal Tile Size:</strong> <span class="tile-size-detail">${tileSize}</span>
          </div>
          <div class="detail-row">
            <strong>Optimization Status:</strong> <span class="status-detail">${status}</span>
          </div>
        </div>
        <div class="optimization-explanation">
          <h4>💡 What does this mean?</h4>
          <p>The backend analyzed your loop and determined the optimal tile size through empirical testing:</p>
          <ul>
            <li><strong>Tile Size ${tileSize}:</strong> This size provides the best balance between cache efficiency and parallelization overhead</li>
            <li><strong>${arrayType}:</strong> The optimization is tailored for this specific array access pattern</li>
            <li><strong>Cache Performance:</strong> Smaller tiles improve cache hit rates, while larger tiles reduce loop overhead</li>
            <li><strong>Memory Locality:</strong> Tiling transforms your loop to access memory in smaller chunks, improving performance</li>
          </ul>
        </div>
        <div class="performance-note">
          <p><strong>🚀 Performance Impact:</strong> Loop tiling can improve performance by 20-60% depending on your hardware and data size.</p>
        </div>
      </div>
    `;

    Swal.fire({
      title: "Tile Size Optimization Details",
      html: detailsHtml,
      icon: "info",
      confirmButtonText: "Got it!",
      width: '600px',
      customClass: {
        popup: 'tile-details-popup'
      }
    });
  };

  const applyBulkOptimization = (optimizationType) => {
    let applicableLoops = loops.filter(loop => {
      if (optimizationType === 'parallel') {
        return loop.Parallelized_Loop && 
               !loop.Parallelized_Loop.includes("Not Parallelizable") && 
               loop.Parallelized_Loop !== "Not Parallelized";
      } else if (optimizationType === 'tiled') {
        return loop.Tiled_Loop && !loop.Tiled_Loop.includes("Not Tiled");
      }
      return false;
    });

    if (applicableLoops.length === 0) {
      Swal.fire({
        title: "No Applicable Loops",
        text: `No loops are available for ${optimizationType} optimization`,
        icon: "info",
        confirmButtonText: "OK",
      });
      return;
    }

    Swal.fire({
      title: `Apply ${optimizationType.charAt(0).toUpperCase() + optimizationType.slice(1)} to All?`,
      text: `This will apply ${optimizationType} optimization to ${applicableLoops.length} loop(s)`,
      icon: "question",
      showCancelButton: true,
      confirmButtonText: `Apply All ${optimizationType.charAt(0).toUpperCase() + optimizationType.slice(1)}`,
      cancelButtonText: "Cancel",
    }).then((result) => {
      if (result.isConfirmed) {
        let appliedCount = 0;
        
        // Apply optimizations silently
        setCodeInput((prevCode) => {
          let newCode = prevCode;
          
          applicableLoops.forEach(loop => {
            const originalLoop = loop.Loop;
            let replacementLoop;
            
            if (optimizationType === 'parallel') {
              replacementLoop = loop.Parallelized_Loop;
            } else if (optimizationType === 'tiled') {
              replacementLoop = loop.Tiled_Loop;
            }
            
            if (replacementLoop) {
              const normalize = (code) =>
                code
                  .replace(/\/\/.*|\/\*[\s\S]*?\*\//g, "")
                  .replace(/([{}();=<>+\-*/%&|\[\]])/g, " $1 ")
                  .replace(/\s+/g, " ")
                  .trim();

              const createPattern = (str) => {
                return normalize(str)
                  .split(" ")
                  .filter((s) => s)
                  .map((s) => s.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&"))
                  .join("\\s*");
              };

              const checkRegex = new RegExp(createPattern(originalLoop), "g");

              if (checkRegex.test(normalize(newCode))) {
                newCode = newCode.replace(checkRegex, () => replacementLoop);
                appliedCount++;
              }
            }
          });
          
          // Remove applied loops from the list
          setLoops((prevLoops) => 
            prevLoops.filter(loop => !applicableLoops.includes(loop))
          );
          
          // Save to session storage
          sessionStorage["ParallelCode"] = newCode;
          
          return newCode;
        });

        Swal.fire({
          title: "Bulk Optimization Complete!",
          text: `${appliedCount} loop(s) optimized with ${optimizationType} version`,
          icon: "success",
          confirmButtonText: "OK",
        });
      }
    });
  };

  return (
    <div className="page-container-pcode">
      <Navbar user={user} />
      <div className="filter-section">
        <h2>Filters</h2>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">Show All</option>
          <option value="parallelized">Parallelized Only</option>
          <option value="tiled">Tiled Only</option>
          <option value="normalized">Has Normalized Version</option>
          <option value="high-complexity">High Complexity (4-5)</option>
          <option value="low-complexity">Low Complexity (1-2)</option>
        </select>
        <button onClick={() => setSortByDifference(!sortByDifference)}>
          {sortByDifference ? "Reset Sorting" : "Sort by Difference"}
        </button>
        <button onClick={() => setSortByComplexity(!sortByComplexity)}>
          {sortByComplexity ? "Reset Complexity Sort" : "Sort by Complexity"}
        </button>
        <button
          className="analytics-btn"
          onClick={() => navigate("/analytics")}
        >
          Get Insights
        </button>
        <div className="bulk-actions">
          <button
            className="bulk-action-btn"
            onClick={() => applyBulkOptimization('parallel')}
          >
            Apply All Parallel
          </button>
          <button
            className="bulk-action-btn"
            onClick={() => applyBulkOptimization('tiled')}
          >
            Apply All Tiled
          </button>
        </div>
      </div>

      <div className="content-container">
        <div className="loop-section">
          {loops.map((loop, index) => {
            // Enhanced filtering logic
            if (
              (filter === "parallelized" &&
                (loop.Parallelized_Loop === "Not Parallelized" || 
                 loop.Parallelized_Loop?.includes("Not Parallelizable"))) ||
              (filter === "tiled" && 
                (loop.Tiled_Loop === "Not Tiled" || 
                 loop.Tiled_Loop?.includes("Not Tiled"))) ||
              (filter === "normalized" && 
                loop.Normalized_Loop === "Already normalized") ||
              (filter === "high-complexity" && 
                (loop.Complexity_Class || 0) < 4) ||
              (filter === "low-complexity" && 
                (loop.Complexity_Class || 0) > 2)
            )
              return null;

            return (
              <div key={index} className="loop-card">
                <div className="loop-header">
                  <h2>Loop {index + 1}</h2>
                  <div className="loop-metadata">
                    <div
                      className={`complexity-badge ${complexityColors[loop.Complexity_Class]}`}
                    >
                      <h3>Complexity Class: {loop.Complexity_Class}</h3>
                    </div>
                    {loop.Complexity && (
                      <div className="complexity-score">
                        <span>Score: {loop.Complexity}</span>
                      </div>
                    )}
                    {loop.Thread_Count && (
                      <div className="thread-count">
                        <span>Recommended Threads: {loop.Thread_Count}</span>
                      </div>
                    )}
                    {loop.Optimal_Tile_Size && (
                      <div 
                        className="tile-size-info clickable" 
                        onClick={() => showTileOptimizationDetails(loop)}
                      >
                        <span>Optimal Tile Size: {loop.Optimal_Tile_Size}</span>
                        <span className="array-type">({loop.Array_Type})</span>
                        <span className="info-icon">ℹ️</span>
                      </div>
                    )}
                    {loop.Tile_Optimization_Status && (
                      <div className="tile-status">
                        <span className={`status-badge ${loop.Tile_Optimization_Status.toLowerCase().replace(' ', '-')}`}>
                          {loop.Tile_Optimization_Status === 'Optimized' ? '⚡' : '🔧'} {loop.Tile_Optimization_Status}
                        </span>
                      </div>
                    )}
                    <div className="optimization-indicators">
                      {loop.Parallelized_Loop && 
                       !loop.Parallelized_Loop.includes("Not Parallelizable") && (
                        <span className="optimization-badge parallel-available">
                          🔄 Parallel
                        </span>
                      )}
                      {loop.Tiled_Loop && 
                       !loop.Tiled_Loop.includes("Not Tiled") && (
                        <span className="optimization-badge tiled-available">
                          🧱 Tiled
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="loop-content">
                  <div className="code-section original">
                    <h3>Original Loop</h3>
                    <SyntaxHighlighter language="cpp" style={oneLight}>
                      {loop.Loop}
                    </SyntaxHighlighter>
                  </div>
                  {loop.Normalized_Loop && loop.Normalized_Loop !== "Already normalized" && (
                    <div className="code-section normalized">
                      <h3>Normalized Loop</h3>
                      <SyntaxHighlighter language="cpp" style={oneLight}>
                        {loop.Normalized_Loop}
                      </SyntaxHighlighter>
                    </div>
                  )}
                  {loop.Parallelized_Loop && 
                   !loop.Parallelized_Loop.includes("Not Parallelizable") && (
                    <div className="code-section parallelized">
                      <h3>Parallelized Loop</h3>
                      <SyntaxHighlighter language="cpp" style={oneLight}>
                        {loop.Parallelized_Loop}
                      </SyntaxHighlighter>
                    </div>
                  )}
                  {loop.Tiled_Loop && 
                   !loop.Tiled_Loop.includes("Not Tiled") && (
                    <div className="code-section tiled">
                      <h3>Tiled Loop</h3>
                      <SyntaxHighlighter language="cpp" style={oneLight}>
                        {loop.Tiled_Loop}
                      </SyntaxHighlighter>
                    </div>
                  )}

                  {(() => {
                    const hasParallel = loop.Parallelized_Loop && 
                                       !loop.Parallelized_Loop.includes("Not Parallelizable") && 
                                       loop.Parallelized_Loop !== "Not Parallelized";
                    const hasTiled = loop.Tiled_Loop && !loop.Tiled_Loop.includes("Not Tiled");
                    
                    if (hasParallel && hasTiled) {
                      return (
                        <button
                          className="configure-btn"
                          onClick={() => replaceLoop(loop)}
                        >
                          Choose & Configure <FaArrowRight />
                        </button>
                      );
                    } else {
                      return (
                        <button
                          className="configure-btn"
                          onClick={() => replaceLoop(loop)}
                        >
                          Configure <FaArrowRight />
                        </button>
                      );
                    }
                  })()}
                </div>
              </div>
            );
          })}
        </div>
        <div className="completed-code-section">
          <h2> Serial Code</h2>
          <SyntaxHighlighter language="cpp" style={oneLight}>
            {codeInput}
          </SyntaxHighlighter>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default ParallelCodePage;
