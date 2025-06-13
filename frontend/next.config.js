/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  productionBrowserSourceMaps: true,
  trailingSlash: false,

  webpack: (config, { isServer }) => {
    config.module.rules.push({
      test: /\.(mp3|wav|ogg)$/,
      use: [{
        loader: 'file-loader',
        options: {
          publicPath: '/_next/static/sounds/',
          outputPath: 'static/sounds/',
          name: '[name].[hash].[ext]',
          esModule: false,
        }
      }]
    });
    config.module.rules.push({
      test: /\.(glsl|vs|fs|vert|frag)$/,
      exclude: /node_modules/,
      use: ['raw-loader', 'glslify-loader']
    });
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack']
    });
    return config;
  },

  async rewrites() {
    return [
      {
        source: '/ollama/:path*',
        destination: `${process.env.OLLAMA_BASE_URL || 'http://localhost:11434'}/:path*`
      },
      {
        source: '/api/chat',
        destination: '/api/chat'
      }
    ];
  },

  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' }
        ]
      }
    ];
  },

  env: {
    OLLAMA_MODEL: process.env.OLLAMA_MODEL || 'llama3',
    NEXT_PUBLIC_APP_NAME: 'AI Chatbot Pro',
    NEXT_PUBLIC_ENABLE_ANALYTICS: process.env.NODE_ENV === 'production' ? 'true' : 'false'
  },

  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/uploads/**'
      }
    ],
    formats: ['image/webp', 'image/avif'],
    minimumCacheTTL: 3600
  },

  // Remove problematic or deprecated experimental flags!
  experimental: {
    // serverActions: true,   // REMOVE THIS LINE!
    // optimizeCss: true,     // REMOVE OR COMMENT THIS LINE IF YOU DON'T NEED IT!
    // workerThreads: true,   // REMOVE OR COMMENT THIS LINE IF YOU DON'T NEED IT!
    scrollRestoration: true,
    instrumentationHook: true
  }
};

module.exports = nextConfig;
