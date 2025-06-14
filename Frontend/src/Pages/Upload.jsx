import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom"; // Import for navigation
import "./Upload.css";
import Navbar from "./NavBar";
import Footer from "./Footer";
import { auth } from "./firebase-config";
import axios from "axios";

const UploadFilesPage = () => {
  const [coreType, setCoreType] = useState("");
  const [ramType, setRamType] = useState("");
  const [processorsCount, setProcessorsCount] = useState("");
  const [codeInput, setCodeInput] = useState("");
  const [parallelizedCode, setParallelizedCode] = useState("");
  const [user, setUser] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationStage, setOptimizationStage] = useState("");

  const navigate = useNavigate(); // Hook for navigation

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((currentUser) => {
      setUser(currentUser);
    });
    return () => unsubscribe();
  }, []);

  const handleAutoRetrieve = () => {
    const userAgent = navigator.userAgent;
    const hardwareConcurrency = navigator.hardwareConcurrency || "Unknown";
    const totalRAM = navigator.deviceMemory || "Unknown";

    setCoreType(userAgent.includes("Win64") ? "64-bit" : "32-bit");
    setProcessorsCount(hardwareConcurrency);
    setRamType(`${totalRAM} GB`);
  };

  const handleSubmit = () => {
    const data = {
      core_type: coreType,
      ram_type: ramType,
      processors_count: processorsCount,
      code: codeInput,
    };
    
    // Start optimization process
    setIsOptimizing(true);
    setOptimizationStage("🔍 Analyzing code structure...");
    
    //  save serial code in session storage
    sessionStorage.setItem("serialCode", codeInput);
    
    // Simulate optimization stages
    const optimizationStages = [
      "🔍 Analyzing code structure...",
      "🧱 Calculating optimal tile sizes...",
      "🔄 Testing parallelization options...", 
      "⚡ Optimizing memory access patterns...",
      "📊 Running empirical performance tests...",
      "✅ Finalizing optimizations..."
    ];
    
    let stageIndex = 0;
    const stageInterval = setInterval(() => {
      if (stageIndex < optimizationStages.length - 1) {
        stageIndex++;
        setOptimizationStage(optimizationStages[stageIndex]);
      }
    }, 1500);
    
    axios
      .post("http://localhost:5000/upload", data)
      .then((response) => {
        clearInterval(stageInterval);
        console.log("Response: ", response);
        if (response.data) {
          setOptimizationStage("✅ Optimization complete!");
          
          // Brief delay to show completion message
          setTimeout(() => {
            setIsOptimizing(false);
            setOptimizationStage("");
            
            // Handle the new JSON structure - the response.data directly contains the loop data
            setParallelizedCode(JSON.stringify(response.data));

            // Navigate to the new page and pass parallelizedCode
            navigate("/parallel-code", {
              state: {
                parallelizedCode: JSON.stringify(response.data),
                codeInput: codeInput,
              },
            });
          }, 1000);
        }
      })
      .catch((error) => {
        clearInterval(stageInterval);
        console.error("Error: ", error);
        setIsOptimizing(false);
        setOptimizationStage("❌ Optimization failed. Please try again.");
        
        // Clear error message after 3 seconds
        setTimeout(() => {
          setOptimizationStage("");
        }, 3000);
      });
  };

  return (
    <div className="page-container">
      <div className="content-wrapper">
        <Navbar user={user} />
        <div className="content">
          <h1 className="heading-u">Fill in the Following Information:</h1>
          <button className="auto-retrieve-btn" onClick={handleAutoRetrieve}>
            Auto Retrieve
          </button>
          <br />
          <br />

          <div className="hardware-section">
            <div className="hardware-input">
              <div className="label">OS Type</div>
              <div className="input-display">
                <div className="grey-box">
                  <input
                    className="white-box"
                    type="text"
                    value={coreType}
                    onChange={(e) => setCoreType(e.target.value)}
                    placeholder="Enter OS Type"
                  />
                </div>
              </div>
            </div>

            <div className="hardware-input">
              <div className="label">RAM Type</div>
              <div className="input-display">
                <div className="grey-box">
                  <input
                    className="white-box"
                    type="text"
                    value={ramType}
                    onChange={(e) => setRamType(e.target.value)}
                    placeholder="Enter RAM Type"
                  />
                </div>
              </div>
            </div>

            <div className="hardware-input">
              <div className="label">Number of Processors</div>
              <div className="input-display">
                <div className="grey-box">
                  <input
                    className="white-box"
                    type="number"
                    value={processorsCount}
                    onChange={(e) => setProcessorsCount(e.target.value)}
                    placeholder="Enter Number of Processors"
                  />
                </div>
              </div>
            </div>
          </div>

          <h1 className="heading1">Upload your files here:</h1>
          <div className="heading-sub">
            Convert your serial code into a parallel one to improve your code's
            performance
          </div>
          <div className="code-section">
            <div className="code-editor">
              <div className="line-numbers">
                {Array.from({
                  length: (codeInput.match(/\n/g) || []).length + 1,
                }).map((_, index) => (
                  <div key={index} className="line-number">
                    {index + 1}
                  </div>
                ))}
              </div>
              <textarea
                className="code-input"
                value={codeInput}
                onChange={(e) => setCodeInput(e.target.value)}
                placeholder="Paste your code here..."
              />
            </div>
          </div>

          <button 
            className="upload-btn" 
            onClick={handleSubmit}
            disabled={isOptimizing}
          >
            {isOptimizing ? "Optimizing..." : "Upload"}
          </button>
          
          {/* Optimization Progress Indicator */}
          {isOptimizing && (
            <div className="optimization-progress">
              <div className="progress-container">
                <div className="progress-spinner"></div>
                <p className="progress-text">{optimizationStage}</p>
                <div className="progress-details">
                  <small>🧱 Finding optimal tile sizes for your loops...</small>
                  <small>⚡ This may take a few moments for complex code</small>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default UploadFilesPage;
