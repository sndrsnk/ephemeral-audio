# Migration Guide - Separate Repo

This directory is ready to be moved to its own repository.

## Steps to Migrate

### 1. Create New Repository
```bash
# On GitHub, create new repo: ephemeral-audio-api
# Then locally:
cd /path/to/new/location
git clone git@github.com:yourusername/ephemeral-audio-api.git
cd ephemeral-audio-api
```

### 2. Copy Files
Copy everything from this `ephemeral-audio/` directory to the new repo root:
```bash
# From your current project root
cp -r ephemeral-audio/* /path/to/ephemeral-audio-api/
```

### 3. Update .gitignore in New Repo
The `.gitignore` in this directory is already configured for the API.

### 4. Remove from 11ty Site
After confirming the new repo works:
```bash
# From your 11ty site repo
rm -rf ephemeral-audio/
git add -A
git commit -m "Move ephemeral-audio to separate repository"
```

### 5. Deploy to Coolify
Follow the instructions in `README.coolify.md` to deploy the new repo.

## What's Already Done

✅ Player moved to 11ty site at `/ephemeral-audio` page
✅ API configured for production with gunicorn
✅ Environment variables documented
✅ Deployment instructions ready

## After Migration

Update the API URL in your 11ty site:
- File: `src/content/ephemeral-audio.njk`
- Line: `const API_BASE_URL = ...`
- Change to: `'https://api.yourdomain.com'`
