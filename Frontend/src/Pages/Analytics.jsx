import React, { useState, useEffect } from "react";
import "./Analytics.css";
import NavBar from "./NavBar";
import Footer from "./Footer";
import axios from "axios";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
} from "chart.js";
import { Line, Bar, Pie, Doughnut } from "react-chartjs-2";

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
  Title
);

const Analytics = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0);
  const [viewMode, setViewMode] = useState("table"); // 'table' or 'graph'
  const [selectedMetric, setSelectedMetric] = useState("");
  const [selectedFileIndex, setSelectedFileIndex] = useState(0); // For table view file selection
  const [messages, setMessages] = useState([
    "HPC systems can perform quadrillions of calculations per second, measured in petaFLOPS.",
    "The first supercomputer, the CDC 6600 (1964), was 1,000 times faster than other computers of its time.",
    "Japan's Fugaku supercomputer held the #1 spot on the TOP500 list from 2020-2021, reaching 442 petaFLOPS.",
    "MPI (Message Passing Interface) is the de facto standard for distributed memory parallel programming.",
    "GPUs can have thousands of cores, while CPUs typically have dozens, making GPUs ideal for parallel workloads.",
    "Amdahl's Law states that the maximum speedup is limited by the portion of code that cannot be parallelized.",
    "Exascale computing (systems capable of at least one exaFLOPS) was achieved in 2022 with Frontier supercomputer.",
    "Weather forecasting models use HPC to process trillions of calculations from millions of observations daily.",
    "The human brain operates at roughly an exaFLOPS, making it comparable to today's fastest supercomputers.",
    "OpenMP is a popular API for shared-memory parallel programming using compiler directives.",
    "Parallel computing faces challenges like race conditions, deadlocks, and load balancing.",
    "Quantum computing may eventually solve certain problems exponentially faster than classical supercomputers.",
    "The TOP500 list, ranking the world's fastest supercomputers, has been published twice yearly since 1993.",
    "CUDA, developed by NVIDIA, is a parallel computing platform enabling GPU acceleration.",
    "Cloud computing has democratized access to HPC through services like AWS ParallelCluster.",
    "Protein folding simulations in medical research can require millions of CPU hours.",
    "Distributed computing projects like Folding@home leverage thousands of volunteer computers worldwide.",
    "Modern HPC systems often consume megawatts of power, enough to power thousands of homes.",
    "Parallel file systems like Lustre can achieve I/O rates of hundreds of gigabytes per second.",
    "The energy efficiency of supercomputers is measured in FLOPS per watt on the Green500 list.",
  ]);

  // Rotate through messages every 3 seconds while loading
  useEffect(() => {
    let interval = null;

    if (loading) {
      interval = setInterval(() => {
        setCurrentMessageIndex((prevIndex) =>
          prevIndex === messages.length - 1 ? 0 : prevIndex + 1
        );
      }, 3000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [loading, messages.length]);

  // Fetch data only once on component mount
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const formData = {
          P_Code: sessionStorage["ParallelCode"],
          S_Code: sessionStorage["serialCode"],
        };

        const response = await axios.post("http://localhost:5000/Analysis", {
          body: formData,
          headers: {
            "Content-Type": "application/json",
          },
        });

        setData(response.data);

        // Set the default selected metric to the first metric (excluding Input File)
        if (response.data && response.data.S_Analysis.length > 0) {
          const metrics = Object.keys(response.data.S_Analysis[0]);
          const firstNonInputMetric = metrics.find(
            (metric) => metric !== "Input File"
          );
          setSelectedMetric(firstNonInputMetric || metrics[0]);
        }
      } catch (error) {
        setError(error);
        console.log(error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []); // Empty dependency array - only runs once on mount

  const toggleViewMode = (mode) => {
    setViewMode(mode);
  };

  const handleMetricSelect = (metric) => {
    setSelectedMetric(metric);
  };

  // Handle file selection for table view
  const handleFileSelect = (index) => {
    setSelectedFileIndex(index);
  };

  // Determine appropriate chart type for each metric
  const getChartTypeForMetric = (metric) => {
    if (metric.includes("Time")) {
      return "line";
    } else if (metric.includes("Usage") || metric.includes("CPU")) {
      return "doughnut";
    } else if (
      metric.includes("Faults") ||
      metric.includes("Switches") ||
      metric.includes("File System")
    ) {
      return "bar";
    } else if (metric.includes("RSS")) {
      return "bar";
    } else {
      return "bar"; // Default
    }
  };

  // Get all file names from the data
  const getFileNames = () => {
    if (!data || !data.S_Analysis) return [];
    
    // Create combined data for sorting
    const combinedData = data.S_Analysis.map((analysis, index) => ({
      fileName: analysis["Input File"] || "Unknown",
      originalIndex: index
    }));

    // Sort by Input File (attempt to sort numerically if possible, otherwise alphabetically)
    combinedData.sort((a, b) => {
      // Try to extract numbers from filenames for numerical sorting
      const extractNumbers = (filename) => {
        const numbers = filename.toString().match(/\d+/g);
        return numbers ? parseInt(numbers[0]) : 0;
      };
      
      const aNum = extractNumbers(a.fileName);
      const bNum = extractNumbers(b.fileName);
      
      // If both have numbers, sort numerically
      if (aNum !== 0 && bNum !== 0) {
        return aNum - bNum;
      }
      
      // Otherwise, sort alphabetically
      return a.fileName.toString().localeCompare(b.fileName.toString());
    });

    return combinedData.map(item => item.fileName);
  };

  // Prepare aggregate chart data for the selected metric across all files
  const prepareAggregateChartData = (metric) => {
    if (!data || !data.S_Analysis || !data.P_Analysis) return null;

    const chartType = getChartTypeForMetric(metric);
    
    // Create combined data for sorting
    const combinedData = data.S_Analysis.map((serialAnalysis, index) => {
      const parallelAnalysis = data.P_Analysis[index];
      return {
        fileName: serialAnalysis["Input File"] || "Unknown",
        serialValue: parseFloat(serialAnalysis[metric]) || 0,
        parallelValue: parseFloat(parallelAnalysis[metric]) || 0,
        originalIndex: index
      };
    });

    // Sort by Input File (attempt to sort numerically if possible, otherwise alphabetically)
    combinedData.sort((a, b) => {
      // Try to extract numbers from filenames for numerical sorting
      const extractNumbers = (filename) => {
        const numbers = filename.toString().match(/\d+/g);
        return numbers ? parseInt(numbers[0]) : 0;
      };
      
      const aNum = extractNumbers(a.fileName);
      const bNum = extractNumbers(b.fileName);
      
      // If both have numbers, sort numerically
      if (aNum !== 0 && bNum !== 0) {
        return aNum - bNum;
      }
      
      // Otherwise, sort alphabetically
      return a.fileName.toString().localeCompare(b.fileName.toString());
    });

    // Extract sorted data
    const fileNames = combinedData.map(item => item.fileName);
    const serialValues = combinedData.map(item => item.serialValue);
    const parallelValues = combinedData.map(item => item.parallelValue);

    if (chartType === "line") {
      return {
        labels: fileNames,
        datasets: [
          {
            label: `Serial ${metric}`,
            data: serialValues,
            borderColor: "rgba(255, 99, 132, 1)",
            backgroundColor: "rgba(255, 99, 132, 0.2)",
            fill: false,
            tension: 0.1,
          },
          {
            label: `Parallel ${metric}`,
            data: parallelValues,
            borderColor: "rgba(54, 162, 235, 1)",
            backgroundColor: "rgba(54, 162, 235, 0.2)",
            fill: false,
            tension: 0.1,
          },
        ],
      };
    } else if (chartType === "bar") {
      return {
        labels: fileNames,
        datasets: [
          {
            label: `Serial ${metric}`,
            data: serialValues,
            backgroundColor: "rgba(255, 99, 132, 0.6)",
            borderColor: "rgba(255, 99, 132, 1)",
            borderWidth: 1,
          },
          {
            label: `Parallel ${metric}`,
            data: parallelValues,
            backgroundColor: "rgba(54, 162, 235, 0.6)",
            borderColor: "rgba(54, 162, 235, 1)",
            borderWidth: 1,
          },
        ],
      };
    } else {
      // For pie charts, we'll use averages instead
      const avgSerial =
        serialValues.reduce((sum, val) => sum + val, 0) / serialValues.length;
      const avgParallel =
        parallelValues.reduce((sum, val) => sum + val, 0) /
        parallelValues.length;

      return {
        labels: ["Average Serial", "Average Parallel"],
        datasets: [
          {
            data: [avgSerial, avgParallel],
            backgroundColor: [
              "rgba(255, 99, 132, 0.6)",
              "rgba(54, 162, 235, 0.6)",
            ],
            borderColor: ["rgba(255, 99, 132, 1)", "rgba(54, 162, 235, 1)"],
            borderWidth: 1,
          },
        ],
      };
    }
  };

  // Render the appropriate chart component for aggregate data
  const renderAggregateChart = (metric) => {
    const chartType = getChartTypeForMetric(metric);
    const chartData = prepareAggregateChartData(metric);

    if (!chartData) return null;

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "top",
        },
        title: {
          display: true,
          text: `${metric} Comparison Across All Files`,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: metric,
          },
        },
        x: {
          title: {
            display: true,
            text: "Input Files",
          },
        },
      },
    };

    switch (chartType) {
      case "line":
        return <Line data={chartData} options={chartOptions} />;
      case "bar":
        return <Bar data={chartData} options={chartOptions} />;
      case "pie":
        return <Pie data={chartData} options={chartOptions} />;
      case "doughnut":
        return <Doughnut data={chartData} options={chartOptions} />;
      default:
        return <Bar data={chartData} options={chartOptions} />;
    }
  };

  // Render individual file data table
  const renderFileDataTable = (fileIndex) => {
    if (
      !data ||
      !data.S_Analysis ||
      !data.P_Analysis ||
      fileIndex >= data.S_Analysis.length
    )
      return null;

    const serialData = data.S_Analysis[fileIndex];
    const parallelData = data.P_Analysis[fileIndex];

    return (
      <div className="table-wrapper">
        <table className="results-table">
          <thead>
            <tr>
              <th>Metric</th>
              <th>Serial</th>
              <th>Parallel</th>
            </tr>
          </thead>
          <tbody>
            {Object.keys(serialData).map((key) => (
              <tr key={key}>
                <td>{key}</td>
                <td>{serialData[key]}</td>
                <td>{parallelData[key]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // Function to generate an aggregate table with data from all files
  const renderAggregateTable = () => {
    if (!data || !data.S_Analysis || !data.P_Analysis) return null;

    const metrics = Object.keys(data.S_Analysis[0]).filter(
      (key) => key !== "Input File"
    );

    // Create combined data for sorting (same logic as chart)
    const combinedData = data.S_Analysis.map((serialAnalysis, index) => {
      const parallelAnalysis = data.P_Analysis[index];
      return {
        fileName: serialAnalysis["Input File"] || "Unknown",
        serialAnalysis: serialAnalysis,
        parallelAnalysis: parallelAnalysis,
        originalIndex: index
      };
    });

    // Sort by Input File (same logic as chart)
    combinedData.sort((a, b) => {
      // Try to extract numbers from filenames for numerical sorting
      const extractNumbers = (filename) => {
        const numbers = filename.toString().match(/\d+/g);
        return numbers ? parseInt(numbers[0]) : 0;
      };
      
      const aNum = extractNumbers(a.fileName);
      const bNum = extractNumbers(b.fileName);
      
      // If both have numbers, sort numerically
      if (aNum !== 0 && bNum !== 0) {
        return aNum - bNum;
      }
      
      // Otherwise, sort alphabetically
      return a.fileName.toString().localeCompare(b.fileName.toString());
    });

    return (
      <table className="results-table">
        <thead>
          <tr>
            <th>File Name</th>
            {metrics.map((metric) => (
              <th key={metric} colSpan="2">
                {metric}
              </th>
            ))}
          </tr>
          <tr>
            <th></th>
            {metrics.map((metric) => (
              <>
                <th key={`${metric}-s`}>Serial</th>
                <th key={`${metric}-p`}>Parallel</th>
              </>
            ))}
          </tr>
        </thead>
        <tbody>
          {combinedData.map((item, index) => (
            <tr key={index}>
              <td>{item.fileName}</td>
              {metrics.map((metric) => (
                <>
                  <td key={`${metric}-s-${index}`}>{item.serialAnalysis[metric]}</td>
                  <td key={`${metric}-p-${index}`}>{item.parallelAnalysis[metric]}</td>
                </>
              ))}
            </tr>
          ))}
          <tr className="total-row">
            <td>
              <strong>Average</strong>
            </td>
            {metrics.map((metric) => {
              const serialAvg =
                combinedData.reduce(
                  (sum, item) => sum + parseFloat(item.serialAnalysis[metric] || 0),
                  0
                ) / combinedData.length;
              const parallelAvg =
                combinedData.reduce(
                  (sum, item) => sum + parseFloat(item.parallelAnalysis[metric] || 0),
                  0
                ) / combinedData.length;
              return (
                <>
                  <td key={`${metric}-s-avg`}>
                    <strong>{serialAvg.toFixed(2)}</strong>
                  </td>
                  <td key={`${metric}-p-avg`}>
                    <strong>{parallelAvg.toFixed(2)}</strong>
                  </td>
                </>
              );
            })}
          </tr>
        </tbody>
      </table>
    );
  };

  // Get all metrics from data (excluding Input File for navigation)
  const getMetrics = () => {
    if (!data || !data.S_Analysis || data.S_Analysis.length === 0) return [];

    return Object.keys(data.S_Analysis[0]).filter(
      (metric) => metric !== "Input File"
    );
  };

  return (
    <div className="main-container">
      <NavBar />
      <div className="analytics-container">
        <div className="page-header">
          <h1>Analytical Results</h1>
        </div>

        {!loading && !error && (
          <div className="view-toggle-container">
            <button
              className={`toggle-button ${viewMode === "table" ? "active" : ""}`}
              onClick={() => toggleViewMode("table")}
            >
              Table View
            </button>
            <button
              className={`toggle-button ${viewMode === "graph" ? "active" : ""}`}
              onClick={() => toggleViewMode("graph")}
            >
              Graph View
            </button>
          </div>
        )}

        {loading ? (
          <div className="loading-container">
            <div className="loader-ring">
              <div></div>
              <div></div>
              <div></div>
              <div></div>
            </div>
            <div className="loading-card">
              <h2>Did You Know?</h2>
              <p>{messages[currentMessageIndex]}</p>
            </div>
          </div>
        ) : error ? (
          <div className="error-message">Error: {error.message}</div>
        ) : (
          <div className="content-container">
            {viewMode === "table" ? (
              <div className="table-container">
                {/* File selection for table view */}
                <div className="file-selection-dropdown">
                  <label htmlFor="file-select">Select Input File</label>
                  <select
                    id="file-select"
                    value={selectedFileIndex}
                    onChange={(e) => handleFileSelect(parseInt(e.target.value))}
                  >
                    {getFileNames().map((fileName, index) => (
                      <option key={index} value={index}>
                        {fileName}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Individual file data table */}
                <h3>Selected File: {getFileNames()[selectedFileIndex]}</h3>
                {renderFileDataTable(selectedFileIndex)}
              </div>
            ) : (
              <div className="graph-view-container">
                {/* Metrics section now at the top */}
                <div className="metrics-sidebar">
                  <h3>Select Metric to Display</h3>
                  <ul className="metrics-list">
                    {getMetrics().map((metric) => (
                      <li key={metric}>
                        <button
                          className={`metric-button ${selectedMetric === metric ? "active" : ""}`}
                          onClick={() => handleMetricSelect(metric)}
                        >
                          {metric}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Chart section now below metrics */}
                <div className="chart-section">
                  <div className="chart-type-info">
                    <p>
                      Chart Type:{" "}
                      <strong>
                        {getChartTypeForMetric(selectedMetric).toUpperCase()}
                      </strong>
                    </p>
                  </div>
                  <div className="chart-container">
                    {selectedMetric && renderAggregateChart(selectedMetric)}
                  </div>
                  <div className="chart-info">
                    <p>Showing {selectedMetric} data across all input files</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
};

export default Analytics;
