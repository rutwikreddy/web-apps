# web-apps
contains all web apps

## Timesheet Tracker
A Streamlit timesheet tracking app with Google OAuth integration for approval and settlement.

### Run locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set Google OAuth credentials in environment variables or Streamlit secrets:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI`
3. Start the app:
   ```bash
   streamlit run app.py
   ```

### Deploy to free hosting
Use Streamlit Community Cloud:
1. Push this folder to a GitHub repository.
2. Create a new Streamlit app from the repo.
3. Add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GOOGLE_REDIRECT_URI` in app secrets.
