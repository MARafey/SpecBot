# SpecBot

An intelligent code optimization platform that automatically analyzes C++ loops and generates optimized parallel and tiled versions for improved performance.

## 🚀 Features

### Core Optimization Capabilities

- **🔄 Loop Parallelization**: Automatic OpenMP parallelization with optimal thread count calculation
- **🧱 Loop Tiling**: Empirical tile size optimization for improved cache performance
- **⚡ Performance Analysis**: Comprehensive benchmarking and performance metrics
- **🎯 Complexity Analysis**: Automatic loop complexity classification (1-5 levels)
- **🔍 Dependency Detection**: Smart analysis of data dependencies for safe parallelization

### User Experience

- **🎨 Interactive Web Interface**: Modern React-based frontend with real-time optimization feedback
- **📊 Visual Results**: Side-by-side comparison of original vs optimized code
- **💡 Educational Insights**: Detailed explanations of optimization techniques and performance impacts
- **⚙️ Hardware-Aware**: Automatic hardware detection and optimization tuning
- **🔄 Bulk Operations**: Apply optimizations to multiple loops simultaneously

### Technical Infrastructure

- **🐳 Docker-based Deployment**: Complete containerized environment
- **🏗️ Microservices Architecture**: Separate backend (Flask) and frontend (React) services
- **🔧 Performance Testing**: Integrated benchmarking with Valgrind and time analysis
- **📈 Analytics Dashboard**: Detailed performance insights and comparison charts

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git
- At least 4GB RAM (recommended for optimal tile size calculations)
- Modern web browser

### Quick Start

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/SpecBot.git
   cd SpecBot
   ```

2. **Start the application:**

   ```bash
   docker-compose up -d
   ```

3. **Access the application:**

   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - Health Check: http://localhost:5000/health

4. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Development Mode

For development with hot reloading:

```bash
docker-compose -f docker-compose.dev.yml up
```

## 🏗️ Architecture

SpecBot follows a modern microservices architecture:

- **🎨 Frontend (React)**:

  - Port: 3000
  - Interactive code editor and optimization dashboard
  - Real-time progress tracking during optimization
  - Educational tooltips and detailed explanations

- **⚙️ Backend (Flask)**:

  - Port: 5000
  - Loop analysis and optimization engine
  - Empirical tile size calculation
  - Performance benchmarking and metrics
  - OpenMP parallelization algorithms

- **🔧 Services**:
  - Automatic hardware detection
  - User authentication (Firebase)
  - Performance analytics and insights

## 📊 How It Works

### 1. Code Analysis

Upload your C++ code, and SpecBot automatically:

- Identifies loops and analyzes their structure
- Determines data dependencies and parallelization opportunities
- Calculates complexity scores (1-5 scale)

### 2. Optimization Process

- **🧱 Tile Size Optimization**: Runs empirical tests to find the optimal tile size for cache performance
- **🔄 Parallelization**: Generates OpenMP directives with optimal thread counts
- **⚡ Performance Testing**: Benchmarks different optimization strategies

### 3. Results & Insights

- View side-by-side comparisons of original vs optimized code
- Get detailed explanations of optimization techniques
- See performance impact estimates (typically 20-60% improvement)
- Export optimized code for immediate use

## 🚀 Usage Example

```cpp
// Original Code
for (int i = 0; i < n; i++) {
    for (int j = 0; j < m; j++) {
        c[i][j] = a[i][j] + b[i][j];
    }
}

// SpecBot Optimized (Tiled + Parallel)
const int TILE_SIZE = 64;  // Empirically determined
#pragma omp parallel for shared(a,b,c) schedule(dynamic) num_threads(4)
for (int i_tile = 0; i_tile < n; i_tile += TILE_SIZE) {
    for (int j_tile = 0; j_tile < m; j_tile += TILE_SIZE) {
        for (int i = i_tile; i < min(i_tile + TILE_SIZE, n); i++) {
            for (int j = j_tile; j < min(j_tile + TILE_SIZE, m); j++) {
                c[i][j] = a[i][j] + b[i][j];
            }
        }
    }
}
```

## 📁 Project Structure

```
SpecBot/
├── Backend/                 # Flask API and optimization engine
│   ├── server.py           # Main Flask application
│   ├── Parinomo.py         # Core optimization algorithms
│   ├── Analysis.py         # Performance analysis tools
│   ├── Inputs/             # Test data for benchmarking
│   └── executables/        # Temporary compilation files
├── Frontend/               # React user interface
│   ├── src/Pages/          # Application pages
│   ├── public/             # Static assets
│   └── package.json        # Dependencies
├── docker-compose.yml      # Production deployment
├── docker-compose.dev.yml  # Development environment
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

- `FLASK_ENV`: Set to `development` for debug mode
- `REACT_APP_API_URL`: Backend API endpoint (default: http://localhost:5000)
- `NODE_ENV`: React environment mode

### Hardware Requirements

- **Minimum**: 2 CPU cores, 4GB RAM
- **Recommended**: 4+ CPU cores, 8GB+ RAM
- **Optimal**: 8+ CPU cores, 16GB+ RAM for complex code analysis

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all Python dependencies are installed
2. **Docker Issues**: Check that ports 3000 and 5000 are available
3. **Performance**: Increase Docker memory allocation for large code analysis
4. **Browser Compatibility**: Use Chrome, Firefox, or Edge for best experience

### Debug Mode

```bash
# Start with debug logging
FLASK_ENV=development docker-compose up
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-optimization`)
3. Commit your changes (`git commit -am 'Add new optimization technique'`)
4. Push to the branch (`git push origin feature/new-optimization`)
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenMP community for parallelization standards
- Valgrind team for performance analysis tools
- React and Flask communities for excellent frameworks
