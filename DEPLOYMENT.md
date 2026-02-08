# Fly.io Deployment - Minimal Cost Configuration

## Live URL
**https://drugs-gov-stats.fly.dev/**

## Deployment Details

- **App Name**: drugs-gov-stats
- **Region**: London (lhr)
- **Machine Type**: shared-cpu-1x
- **Memory**: 256MB
- **Status**: Deployed and running

## Cost Optimization Features

Your deployment is configured for **minimal cost**:

1. **Auto-stop machines**: Machines stop when idle (no traffic)
2. **Auto-start machines**: Machines start automatically when traffic arrives
3. **Min machines running**: 0 (no machines running when idle = $0/month when not in use)
4. **Smallest machine size**: 256MB RAM, shared CPU
5. **Single worker**: Only 1 gunicorn worker to minimize memory usage
6. **No high availability**: Single machine (HA disabled with `--ha=false`)

### Expected Costs

With this configuration:
- **When idle** (no visitors): ~$0/month (machines stopped)
- **When active**: ~$1.94/month for shared-cpu-1x @ 256MB
- **First 3 machines** on Fly.io are included in the free tier

This means your app will likely cost **$0/month** unless you have sustained high traffic.

## How It Works

1. When someone visits your app, Fly.io automatically starts the machine (takes ~1-2 seconds)
2. The machine stays running while there's traffic
3. After being idle for a period, the machine automatically stops
4. No charges while the machine is stopped

## Useful Commands

```bash
# Check app status
flyctl status

# View logs
flyctl logs

# Open app in browser
flyctl open

# SSH into machine
flyctl ssh console

# Scale machine (if needed)
flyctl scale memory 512  # increase to 512MB if needed
flyctl scale count 2     # add more machines (increases cost)

# Monitor costs
flyctl dashboard metrics

# Stop/start manually
flyctl machine stop <machine-id>
flyctl machine start <machine-id>

# Destroy app (to stop all charges)
flyctl apps destroy drugs-gov-stats
```

## Files Created

- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration
- `fly.toml` - Fly.io deployment configuration
- `Procfile` - Process definition (for reference)

## Next Steps

1. Visit https://drugs-gov-stats.fly.dev/ to see your live app
2. Monitor usage at https://fly.io/apps/drugs-gov-stats
3. The first cold start may take 1-2 seconds as the machine spins up

Enjoy your minimal-cost deployment!
