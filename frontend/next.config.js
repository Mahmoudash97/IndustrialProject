/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  // API Proxying Configuration
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_URL ? 
          `${process.env.NEXT_PUBLIC_API_URL}/:path*` : 
          'http://localhost:8000/:path*',
      },
    ];
  },

  // Image optimization configuration
  images: {
    domains: ['localhost'],
    formats: ['image/webp', 'image/avif'],
  },

  // Headers for additional security and performance
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },

  // Environment variables to expose to frontend
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // Webpack configuration for optimal bundling
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Important: return the modified config
    return config;
  },
};

module.exports = nextConfig;
