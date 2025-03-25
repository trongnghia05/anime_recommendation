# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package.json và cài đặt dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy tất cả files
COPY . .

# Build ứng dụng
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files từ build stage
COPY --from=build /app/build /usr/share/nginx/html

# Cấu hình Nginx để hỗ trợ React Router
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]