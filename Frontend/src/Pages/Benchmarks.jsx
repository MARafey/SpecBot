import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import NavBar from "./NavBar";
import Footer from "./Footer";
import "./Benchmarks.css";

const Benchmarks = () => {
  const navigate = useNavigate();
  const [benchmarkData, setBenchmarkData] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState("User Time (s)");
  const [githubRepo, setGithubRepo] = useState(
    "https://github.com/MARafey/HPC-Comparision"
  );

  const metrics = ["User Time (s)", "System Time (s)", "Elapsed Time (s)"];

  // Define colors for each approach
  const colorMap = {
    normal: "#FF5733",
    claude: "#33A8FF",
    gpt: "#33FF57",
    Gemini: "#F033FF",
    Parinomo: "#FFD700",
    viennacl: "#8A2BE2",
  };

  // Display names mapping
  const displayNames = {
    normal: "Normal",
    claude: "Claude",
    gpt: "ChatGPT",
    Gemini: "Gemini",
    Parinomo: "Parinomo",
    viennacl: "ViennaCL",
  };

  useEffect(() => {
    const fetchBenchmarkData = async () => {
      try {
        setLoading(true);

        // List of benchmark files to fetch
        const benchmarkFiles = [
          "Resultsnormal.csv",
          "Resultsclaude.csv",
          "Resultsgpt.csv",
          "ResultsGemini.csv",
          "ResultsParinomo.csv",
          "Resultsviennacl.csv",
        ];

        const results = {};

        // Fetch and parse each CSV file
        for (const file of benchmarkFiles) {
          const response = await fetch(`/Benchmarks/${file}`);
          const csvText = await response.text();

          // Parse CSV content
          const rows = csvText.split("\n");
          const headers = rows[0].split(",");

          // Extract the approach name from the file name (remove "Results" prefix and ".csv" suffix)
          const approachName = file.replace("Results", "").replace(".csv", "");

          // Process data
          const data = [];
          for (let i = 1; i < rows.length; i++) {
            if (rows[i].trim() === "") continue;

            const values = rows[i].split(",");
            const rowData = {};

            headers.forEach((header, index) => {
              rowData[header] = values[index] ? parseFloat(values[index]) : 0;
            });

            data.push(rowData);
          }

          results[approachName] = data;
        }

        setBenchmarkData(results);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching benchmark data:", error);
        setLoading(false);
      }
    };

    fetchBenchmarkData();
  }, []);

  // Prepare data for charting
  const prepareChartData = () => {
    const chartData = [];

    // If data is not loaded yet, return empty array
    if (loading || Object.keys(benchmarkData).length === 0) {
      return chartData;
    }

    // Get all unique matrix sizes
    const sizes = new Set();
    Object.values(benchmarkData).forEach((approach) => {
      approach.forEach((point) => {
        sizes.add(point.Size);
      });
    });

    // Sort sizes numerically
    const sortedSizes = Array.from(sizes).sort((a, b) => a - b);

    // Create data points for each size
    sortedSizes.forEach((size) => {
      const dataPoint = { Size: size };

      Object.entries(benchmarkData).forEach(([approach, data]) => {
        const matchingPoint = data.find((point) => point.Size === size);
        if (matchingPoint) {
          dataPoint[approach] = matchingPoint[selectedMetric];
        }
      });

      chartData.push(dataPoint);
    });

    return chartData;
  };

  const chartData = prepareChartData();

  return (
    <div className="benchmarks-page">
      <NavBar />
      <div className="benchmarks-container">
        <h1 className="benchmarks-main-title">Benchmarks</h1>
        <h2 className="benchmarks-title">Performance Comparison</h2>
        <p className="benchmarks-description">
          This page shows the performance comparison of different approaches to
          matrix multiplication, which is one of the main computationally
          expensive tasks done in many software and machine learning algorithms.
        </p>

        <div className="github-link">
          <a href={githubRepo} target="_blank" rel="noopener noreferrer">
            <img
              src={process.env.PUBLIC_URL + "/github-logo.jpg"}
              alt="GitHub"
              width="28"
              height="28"
              style={{ marginRight: "10px" }}
            />
            View on GitHub
          </a>
        </div>

        <div className="benchmarks-content">
          <div className="metrics-selector">
            <h3>Select Metric</h3>
            {metrics.map((metric) => (
              <button
                key={metric}
                className={`metric-button ${selectedMetric === metric ? "active" : ""}`}
                onClick={() => setSelectedMetric(metric)}
              >
                {metric}
              </button>
            ))}
          </div>

          <div className="chart-container">
            {loading ? (
              <div className="loading">Loading benchmark data...</div>
            ) : (
              <ResponsiveContainer width="100%" height={500}>
                <LineChart
                  data={chartData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 10 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="Size"
                    label={{
                      value: "Matrix Size",
                      position: "insideBottomRight",
                      offset: -10,
                    }}
                    scale="log"
                    domain={["auto", "auto"]}
                  />
                  <YAxis
                    label={{
                      value: selectedMetric,
                      angle: -90,
                      position: "insideLeft",
                    }}
                  />
                  <Tooltip formatter={(value) => value.toFixed(3)} />
                  <Legend />

                  {Object.keys(benchmarkData).map((approach) => (
                    <Line
                      key={approach}
                      type="monotone"
                      dataKey={approach}
                      name={displayNames[approach] || approach}
                      stroke={colorMap[approach]}
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Benchmarks;
