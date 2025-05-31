module.exports = {
  apps: [{
    name: 'plaza-scraper',
    script: 'scraper.py',
    interpreter: 'python3',
    cwd: '/path/to/your/scraper', // Update this to your actual VPS path
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    },
    error_file: './logs/err.log',
    out_file: './logs/out.log',
    log_file: './logs/combined.log',
    time: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    // Restart policy
    restart_delay: 4000,
    max_restarts: 10,
    min_uptime: '10s',
    // Monitoring
    pmx: true,
    // Auto restart on crash
    kill_timeout: 1600,
    listen_timeout: 3000,
    // Environment variables (you can add more here)
    env_production: {
      NODE_ENV: 'production'
    }
  }]
} 