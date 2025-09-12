# Scrub-a-dub Hub

Office duty assignment bot that fairly rotates coffee machine and fridge cleaning duties among team 
members for Channable's US office. 

## Overview

This is a Python-based Google Cloud Functions application that:
- Assigns coffee machine cleaning duties biweekly (odd weeks)
- Assigns fridge cleaning duties monthly (last Wednesday of the month)
- Sends notifications via Mattermost webhooks
- Tracks assignments in a PostgresQL database to ensure fair rotation
- Automatically resets cycles when everyone has had a turn

## Architecture

The application uses:
- **Google Cloud Functions**: Two separate HTTP-triggered functions
- **PostgreSQL (Neon)**: Stores member data and duty assignments
- **Google Secret Manager**: Securely stores database connection strings
- **Mattermost Webhooks**: Sends notifications to office channel

## Database Schema

```sql
-- Office members
members (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  full_name VARCHAR(100),
  coffee_drinker BOOLEAN DEFAULT true,
  active BOOLEAN DEFAULT true
)

-- Duty assignments
duty_assignments (
  id SERIAL PRIMARY KEY,
  member_id INTEGER REFERENCES members(id),
  duty_type VARCHAR(20), -- 'coffee' or 'fridge'
  assigned_at TIMESTAMP DEFAULT NOW(),
  cycle_id INTEGER
)
```

## Deployment

### Prerequisites

1. **Google Cloud Project** with enabled APIs:
   - Cloud Functions
   - Secret Manager
   - Cloud Build (for GitHub integration)

2. **Neon PostgreSQL Database**:
   - Sign up at [neon.tech](https://neon.tech)
   - Create database with schema above
   - Store connection strings in Secret Manager:
     - `neon-database-connection-string` (production)
     - `neon-database-connection-string-dev` (development)

3. **Mattermost Webhook URL**:
   - Create incoming webhook in Mattermost
   - Set as environment variable during deployment

### Automated Deployment (GitHub)

1. **Connect GitHub to Cloud Build**:
   ```bash
   # In Google Cloud Console: Cloud Build > Triggers
   # Click "Connect Repository" and authorize GitHub
   ```

2. **Create Build Trigger**:
   ```bash
   gcloud builds triggers create github \
     --repo-name=java-janitor \
     --repo-owner=YOUR_GITHUB_USERNAME \
     --branch-pattern="^main$" \
     --build-config=cloudbuild.yaml
   ```

3. **Configure Secrets**: Add `MATTERMOST_WEBHOOK_URL` as substitution variable in trigger settings

Now pushing to `main` automatically deploys both functions.

## Local Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MATTERMOST_WEBHOOK_URL=your_webhook_url
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
```

### Testing

```bash
# Run functions framework locally
functions-framework --target=assign_coffee_duty --debug --port=8080

# Test coffee duty (in another terminal)
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"test_mode": true}'

# Test fridge duty (restart with different target)
functions-framework --target=assign_fridge_duty --debug --port=8080

curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"test_mode": true}'
```

In test mode, notifications go to `@lotte_lutkenhaus` instead of the office channel.

## Managing Members

Members are stored in the PostgreSQL database. To add/remove members:

```sql
-- Add a new member
INSERT INTO members (username, full_name, coffee_drinker, active) 
VALUES ('john_doe', 'John Doe', true, true);

-- Deactivate a member (preserves history)
UPDATE members SET active = false WHERE username = 'john_doe';

-- Mark someone as non-coffee drinker
UPDATE members SET coffee_drinker = false WHERE username = 'john_doe';
```

## Scheduling

Schedule these Cloud Functions to run weekly:

1. **Coffee Duty**: Every Tuesday (checks if odd week)
   ```bash
   gcloud scheduler jobs create http coffee-duty-scheduler \
     --schedule="0 16 * * 2" \
     --uri=YOUR_COFFEE_FUNCTION_URL \
     --http-method=POST \
     --message-body='{"test_mode": false}'
   ```

2. **Fridge Duty**: Every Wednesday (checks if last of month)
   ```bash
   gcloud scheduler jobs create http fridge-duty-scheduler \
     --schedule="0 16 * * 3" \
     --uri=YOUR_FRIDGE_FUNCTION_URL \
     --http-method=POST \
     --message-body='{"test_mode": false}'
   ```