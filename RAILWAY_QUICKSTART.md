# Quick Start: Railway Deployment

## Deploy in 5 Minutes

### Option 1: Deploy via Railway CLI (Fastest)

```bash
# 1. Install Railway CLI
npm i -g @railway/cli

# 2. Navigate to MCP server directory
cd mcp-server

# 3. Login to Railway
railway login

# 4. Create new project
railway init

# 5. Deploy!
railway up
```

That's it! Railway will give you a URL.

### Option 2: Deploy via GitHub

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-github-repo>
   git push -u origin main
   ```

2. **Connect to Railway**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Select `mcp-server` as root directory
   - Click "Deploy"

### Option 3: One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/mcp-server)

Click the button and follow the prompts.

## After Deployment

1. **Get Your Server URL**
   - Railway will provide a URL like: `https://your-app.railway.app`
   - Copy this URL

2. **Configure Your Client**
   Create `.env` file in project root:
   ```env
   MCP_SERVER_MODE=remote
   MCP_SERVER_URL=https://your-app.railway.app
   ```

3. **Test the Connection**
   ```bash
   python test_mcp_server.py
   ```

4. **Run Your Calculator**
   ```bash
   python main.py
   ```

## Troubleshooting

### Server Won't Start
- Check Railway logs: `railway logs`
- Verify all dependencies in `requirements.txt`
- Ensure `Procfile` is present

### Client Can't Connect
- Verify server URL is correct
- Check Railway server is running (not sleeping)
- Test with: `curl https://your-app.railway.app/health`

### Build Fails
- Clear build cache in Railway dashboard
- Check Python version compatibility
- Verify all imports are in `requirements.txt`

## What Gets Deployed?

```
mcp-server/
├── server.py          ✓ Main server code
├── requirements.txt   ✓ Python dependencies
├── Procfile          ✓ Start command
└── railway.json      ✓ Railway config
```

## Environment Variables (Optional)

Set in Railway dashboard if needed:
- `PYTHON_VERSION=3.11`
- `PORT=8080` (Railway sets this automatically)

## Cost

- Railway free tier: 500 hours/month
- Perfect for personal projects
- Upgrade for production use

## Next Steps

- ✅ Server deployed
- ✅ Client configured
- ⬜ Test all tools
- ⬜ Build desktop app
- ⬜ Deploy mobile app

## Support

- Railway Docs: https://docs.railway.app
- MCP Docs: https://modelcontextprotocol.io
- Issues: Create issue in repository
