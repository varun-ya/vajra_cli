FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN if [ -f package.json ]; then npm install; fi

# Copy function code
COPY . .

# Install Vajra runtime dependencies
RUN npm install express @google-cloud/logging

# Copy runtime wrapper
COPY vajra_runtime.js .

EXPOSE 8080

CMD ["node", "vajra_runtime.js"]