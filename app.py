import os
from datetime import date

import streamlit as st
from authlib.integrations.requests_client import OAuth2Session

st.set_page_config(page_title="Timesheet Tracker", page_icon="🕒", layout="wide")

AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"
SCOPE = ["openid", "email", "profile"]

TASK_OPTIONS = ["Development", "Analysis", "Design", "Meeting"]


def get_google_oauth_config():
    client_id = st.session_state.get(
        "google_client_id",
        st.secrets.get("GOOGLE_CLIENT_ID", os.getenv("GOOGLE_CLIENT_ID")),
    )
    client_secret = st.session_state.get(
        "google_client_secret",
        st.secrets.get("GOOGLE_CLIENT_SECRET", os.getenv("GOOGLE_CLIENT_SECRET")),
    )
    redirect_uri = st.session_state.get(
        "google_redirect_uri",
        st.secrets.get("GOOGLE_REDIRECT_URI", os.getenv("GOOGLE_REDIRECT_URI")),
    )
    return client_id, client_secret, redirect_uri


def create_oauth_session(client_id, client_secret, redirect_uri, state=None):
    return OAuth2Session(
        client_id,
        client_secret,
        scope=SCOPE,
        redirect_uri=redirect_uri,
        state=state,
    )


def authorize_url(client_id, client_secret, redirect_uri):
    oauth = create_oauth_session(client_id, client_secret, redirect_uri)
    auth_url, state = oauth.create_authorization_url(
        AUTHORIZATION_ENDPOINT,
        access_type="offline",
        prompt="consent",
    )
    st.session_state.oauth_state = state
    return auth_url


def fetch_google_user(code, client_id, client_secret, redirect_uri):
    oauth = create_oauth_session(
        client_id,
        client_secret,
        redirect_uri,
        state=st.session_state.get("oauth_state"),
    )
    token = oauth.fetch_token(
        TOKEN_ENDPOINT,
        code=code,
        client_secret=client_secret,
    )
    user_info = oauth.get(USERINFO_ENDPOINT).json()
    return token, user_info


def init_rows():
    if "rows" not in st.session_state:
        st.session_state.rows = [
            {
                "date": date.today(),
                "hours": 0.0,
                "task": TASK_OPTIONS[0],
                "description": "",
                "rate": 0.0,
                "approved": False,
                "settled": False,
            }
        ]


def create_oauth_session(client_id, client_secret, redirect_uri, state=None):
    return OAuth2Session(
        client_id,
        client_secret,
        scope=SCOPE,
        redirect_uri=redirect_uri,
        state=state,
    )


def fetch_google_user(code, client_id, client_secret, redirect_uri):
    oauth = create_oauth_session(
        client_id,
        client_secret,
        redirect_uri,
        state=st.session_state.get("oauth_state"),
    )
    token = oauth.fetch_token(
        TOKEN_ENDPOINT,
        code=code,
        client_secret=client_secret,
    )
    user_info = oauth.get(USERINFO_ENDPOINT).json()
    return token, user_info


def process_auth_callback():
    client_id, client_secret, redirect_uri = get_google_oauth_config()
    query_params = st.experimental_get_query_params()
    code = query_params.get("code", [None])[0]
    state = query_params.get("state", [None])[0]
    if code and state and st.session_state.get("oauth_state") == state:
        if not all([client_id, client_secret, redirect_uri]):
            st.error("Google OAuth configuration is missing. Enter client details in the OAuth configuration section.")
            return
        try:
            _, user_info = fetch_google_user(code, client_id, client_secret, redirect_uri)
            st.session_state.google_user = {
                "email": user_info.get("email"),
                "name": user_info.get("name"),
            }
            st.experimental_set_query_params()
        except Exception:
            st.error("Google authentication failed. Check your redirect URI and app configuration.")
            st.session_state.google_user = None


def add_row():
    st.session_state.rows.append(
        {
            "date": date.today(),
            "hours": 0.0,
            "task": TASK_OPTIONS[0],
            "description": "",
            "rate": 0.0,
            "approved": False,
            "settled": False,
        }
    )


def main():
    st.title("Timesheet Tracking App")
    st.write(
        "Track daily work hours, task types, event details, approval status, and settlement amounts with Google authentication."
    )

    init_rows()
    process_auth_callback()

    client_id, client_secret, redirect_uri = get_google_oauth_config()
    auth_configured = all([client_id, client_secret, redirect_uri])

    st.info(
        "Enter Google OAuth client details below if you want to sign in during this session."
    )

    with st.expander("Google OAuth configuration", expanded=not auth_configured):
        st.text_input(
            "Google Client ID",
            value=client_id or "",
            key="google_client_id",
        )
        st.text_input(
            "Google Client Secret",
            value=client_secret or "",
            key="google_client_secret",
            type="password",
        )
        st.text_input(
            "Google Redirect URI",
            value=redirect_uri or "http://localhost:8501/",
            key="google_redirect_uri",
        )
        st.caption(
            "These values are used only for the current session and are not stored persistently in the app."
        )

    auth_col, _, status_col = st.columns([3, 1, 2])
    with auth_col:
        if st.session_state.get("google_user"):
            st.success(f"Signed in as {st.session_state.google_user['email']}")
        else:
            if auth_configured:
                auth_url = authorize_url(client_id, client_secret, redirect_uri)
                st.markdown(
                    f"<a href=\"{auth_url}\" style=\"display:inline-block;padding:10px 16px;background:#4285F4;color:white;border-radius:6px;text-decoration:none;\">Login with Google</a>",
                    unsafe_allow_html=True,
                )
            else:
                st.warning(
                    "Enter your Google OAuth credentials above to sign in on the fly."
                )

    with status_col:
        if st.session_state.get("google_user"):
            if st.button("Logout"):
                st.session_state.google_user = None
                st.experimental_rerun()

    st.markdown("---")

    add_col, _, total_col = st.columns([2, 1, 3])
    with add_col:
        if st.button("+ Add row"):
            add_row()
    with total_col:
        st.write("### Summary")
        total_amount = sum(r["hours"] * r["rate"] for r in st.session_state.rows)
        settled_amount = sum(
            r["hours"] * r["rate"] for r in st.session_state.rows if r["settled"]
        )
        remaining_amount = total_amount - settled_amount
        st.metric("Total amount (INR)", f"₹{total_amount:,.2f}")
        st.metric("Settled amount (INR)", f"₹{settled_amount:,.2f}")
        st.metric("Remaining amount (INR)", f"₹{remaining_amount:,.2f}")

    st.write("#### Timesheet entries")
    for idx, row in enumerate(st.session_state.rows):
        card = st.container()
        with card:
            cols = st.columns([2, 1, 2, 3, 1, 1])
            cols[0].date_input(
                "Date",
                value=row["date"],
                key=f"date_{idx}",
                on_change=lambda i=idx: st.session_state.rows.__setitem__(i, st.session_state.rows[i]),
            )
            st.session_state.rows[idx]["date"] = st.session_state.get(f"date_{idx}", row["date"])
            cols[1].number_input(
                "Hours",
                min_value=0.0,
                value=row["hours"],
                step=0.25,
                key=f"hours_{idx}",
            )
            st.session_state.rows[idx]["hours"] = st.session_state.get(f"hours_{idx}", row["hours"])
            cols[2].selectbox(
                "Task",
                TASK_OPTIONS,
                index=TASK_OPTIONS.index(row["task"] if row["task"] in TASK_OPTIONS else TASK_OPTIONS[0]),
                key=f"task_{idx}",
            )
            st.session_state.rows[idx]["task"] = st.session_state.get(f"task_{idx}", row["task"])
            cols[3].text_area(
                "Description",
                value=row["description"],
                key=f"description_{idx}",
                height=100,
            )
            st.session_state.rows[idx]["description"] = st.session_state.get(
                f"description_{idx}", row["description"]
            )
            cols[4].number_input(
                "Base rate (INR)",
                min_value=0.0,
                value=row["rate"],
                step=50.0,
                key=f"rate_{idx}",
            )
            st.session_state.rows[idx]["rate"] = st.session_state.get(f"rate_{idx}", row["rate"])
            approval_col, settle_col = st.columns(2)
            if st.session_state.get("google_user"):
                if approval_col.button(
                    "Approve",
                    key=f"approve_{idx}",
                ):
                    st.session_state.rows[idx]["approved"] = True
                settled = settle_col.checkbox(
                    "Settled",
                    value=row["settled"],
                    key=f"settled_{idx}",
                )
                st.session_state.rows[idx]["settled"] = settled
            else:
                approval_col.write("Login to approve and settle")
                settle_col.write("Google auth required")

            status = "Approved" if row["approved"] else "Pending approval"
            settled_status = "Settled" if row["settled"] else "Unsettled"
            st.info(f"Status: {status} • {settled_status}")
            st.markdown("---")

    display_rows = [
        {
            "Date": r["date"].strftime("%Y-%m-%d"),
            "Hours": r["hours"],
            "Task": r["task"],
            "Description": r["description"],
            "Rate (INR)": r["rate"],
            "Approved": "Yes" if r["approved"] else "No",
            "Settled": "Yes" if r["settled"] else "No",
        }
        for r in st.session_state.rows
    ]

    st.dataframe(display_rows, use_container_width=True)


if __name__ == "__main__":
    main()
