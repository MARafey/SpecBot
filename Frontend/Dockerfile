# Making docker image for frontend
# Using node image
FROM node:18.17.0

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Setting working directory
WORKDIR /app

# Copying package.json and package-lock.json
COPY package*.json ./

# Installing dependencies
RUN npm install

# Copying all files
COPY . .

# Create build directory
RUN mkdir -p build

# Exposing port 3000
EXPOSE 3000

# Running the app in development mode (use npm run build && npm install -g serve && serve -s build for production)
CMD ["npm", "start"]
