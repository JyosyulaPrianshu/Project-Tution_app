# Render PostgreSQL Database Connection Guide

## 🔧 DBeaver Connection Issues - Solutions

### **Problem: EOF Exception in DBeaver**

This is a common issue when connecting to Render's PostgreSQL database from DBeaver.

## 🎯 Step-by-Step Solution

### **1. Get the Correct Connection String**

In your Render dashboard:
1. Go to your **PostgreSQL database**
2. Click on **"Connect"**
3. Copy the **"External Database URL"** (not the internal one)
4. It should look like: `postgresql://username:password@host:port/database`

### **2. DBeaver Connection Settings**

#### **General Tab:**
- **Host**: Extract from your connection string
- **Port**: Usually `5432`
- **Database**: Your database name
- **Username**: Your username
- **Password**: Your password

#### **Driver Properties Tab (IMPORTANT):**
- **ssl**: `true`
- **sslmode**: `require`
- **connectTimeout**: `30`
- **socketTimeout**: `30`

### **3. Test Connection with Python**

Run the test script I created:

```bash
# Set your DATABASE_URL environment variable
export DATABASE_URL="postgresql://username:password@host:port/database"

# Run the test
python test_db_connection.py
```

### **4. Common Issues & Fixes**

#### **Issue 1: SSL Connection Required**
**Error**: `SSL connection is required`
**Solution**: 
- In DBeaver → Driver Properties → Set `ssl` to `true`
- Set `sslmode` to `require`

#### **Issue 2: Connection Timeout**
**Error**: `Connection timed out`
**Solution**:
- Check your internet connection
- Try from a different network
- Increase `connectTimeout` to `60`

#### **Issue 3: Authentication Failed**
**Error**: `Authentication failed`
**Solution**:
- Double-check username/password
- Make sure you're using the External Database URL
- Verify the database name is correct

#### **Issue 4: Host Not Found**
**Error**: `Could not connect to server`
**Solution**:
- Check the hostname in your connection string
- Try pinging the host
- Check if your IP is whitelisted

## 🔍 Alternative Connection Methods

### **Method 1: Command Line (psql)**
```bash
# Install PostgreSQL client
# Ubuntu/Debian:
sudo apt-get install postgresql-client

# macOS:
brew install postgresql

# Windows:
# Download from https://www.postgresql.org/download/windows/

# Connect:
psql "postgresql://username:password@host:port/database?sslmode=require"
```

### **Method 2: pgAdmin**
1. Download pgAdmin from https://www.pgadmin.org/
2. Create new server connection
3. Use the same connection details
4. Enable SSL in connection settings

### **Method 3: Online Database Tools**
- **Supabase Dashboard** (if using Supabase)
- **Railway Dashboard** (if using Railway)
- **Heroku Data Dashboard** (if using Heroku)

## 🚨 Important Notes

### **1. Use External Database URL**
- Render provides two URLs: **Internal** and **External**
- Always use the **External Database URL** for connections from your local machine
- Internal URL only works from within Render's network

### **2. SSL is Mandatory**
- Render requires SSL connections
- Never disable SSL in your connection settings
- Use `sslmode=require` or `sslmode=verify-full`

### **3. Connection Limits**
- Free tier has connection limits
- Close connections when not in use
- Use connection pooling in production

## 🛠️ Troubleshooting Checklist

- [ ] Using External Database URL (not Internal)
- [ ] SSL enabled (`ssl=true`, `sslmode=require`)
- [ ] Correct hostname, port, database name
- [ ] Correct username and password
- [ ] No firewall blocking connection
- [ ] Internet connection stable
- [ ] Database is running (check Render dashboard)

## 📞 Getting Help

If you're still having issues:

1. **Check Render Status**: https://status.render.com/
2. **Render Documentation**: https://render.com/docs/databases
3. **Community Support**: https://community.render.com/

## 🎯 Next Steps

Once connected successfully:

1. **Run your Flask migrations**:
   ```bash
   flask db upgrade
   ```

2. **Test your application**:
   ```bash
   python test_db_connection.py
   ```

3. **Deploy to Render** with the database connection

## 💡 Pro Tips

- **Save connection details** in a secure password manager
- **Use environment variables** for database URLs
- **Test connections** before deploying
- **Monitor database usage** in Render dashboard
- **Set up backups** for production databases 