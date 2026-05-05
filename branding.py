"""Visual branding for the Streamlit app — aligned with SimpleTest (simpletest.ai).

Colours: slate navy hero, indigo→sky accent gradient, light cool-grey canvas.
Does not load remote assets except Google Fonts (same origin policy friendly).
"""

from __future__ import annotations

import streamlit as st

BRAND_WEBSITE = "https://simpletest.ai"
BRAND_APP = "https://app.simpletest.ai/"
BRAND_PLATFORM = "https://simpletest.ai/platform.html"


def inject_theme_css() -> None:
    """Inject global CSS once per run (safe to call every rerun)."""
    st.markdown(
        """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap" rel="stylesheet">

<style>
  /* Root tokens */
  :root {
    --st-brand-navy: #0f172a;
    --st-brand-slate: #1e293b;
    --st-brand-indigo: #6366f1;
    --st-brand-sky: #38bdf8;
    --st-brand-muted: #64748b;
    --st-brand-border: #e2e8f0;
    --st-brand-surface: #ffffff;
    --st-brand-canvas: #f4f7fb;
  }

  html, body, [class*="css"]  {
    font-family: "DM Sans", ui-sans-serif, system-ui, -apple-system, sans-serif !important;
  }

  .stApp {
    background: linear-gradient(180deg, var(--st-brand-canvas) 0%, #eef2f7 100%) !important;
  }

  /* Main column breathing room */
  .block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 3rem !important;
    max-width: 1200px !important;
  }

  /* Hero */
  .st-brand-hero {
    background: linear-gradient(135deg, var(--st-brand-navy) 0%, var(--st-brand-slate) 55%, #0c4a6e 100%);
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.25rem;
    color: #f8fafc;
    box-shadow: 0 12px 40px rgba(15, 23, 42, 0.25);
  }
  .st-brand-hero-inner {
    display: flex;
    align-items: flex-start;
    gap: 1.25rem;
    flex-wrap: wrap;
  }
  .st-brand-mark {
    flex-shrink: 0;
    width: 52px;
    height: 52px;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--st-brand-indigo), var(--st-brand-sky));
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: -0.02em;
    color: #fff;
    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35);
  }
  .st-brand-title {
    font-size: 1.55rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    line-height: 1.2;
    margin: 0 0 0.35rem 0;
  }
  .st-brand-pill {
    display: inline-block;
    margin-left: 0.35rem;
    padding: 0.15rem 0.55rem;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-radius: 999px;
    background: rgba(56, 189, 248, 0.2);
    color: #e0f2fe;
    vertical-align: middle;
  }
  .st-brand-sub {
    font-size: 0.95rem;
    color: #cbd5e1;
    line-height: 1.45;
    margin: 0 0 0.85rem 0;
    max-width: 52rem;
  }
  .st-brand-links {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.25rem;
  }
  .st-brand-links a {
    color: #7dd3fc !important;
    font-weight: 500;
    font-size: 0.9rem;
    text-decoration: none !important;
    border-bottom: 1px solid rgba(125, 211, 252, 0.35);
  }
  .st-brand-links a:hover {
    color: #fff !important;
    border-bottom-color: #fff;
  }

  /* Tabs — pill-style nav */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0.35rem;
    background-color: rgba(255, 255, 255, 0.85);
    padding: 0.35rem;
    border-radius: 12px;
    border: 1px solid var(--st-brand-border);
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 0.55rem 1.1rem;
    font-weight: 600;
    font-size: 0.92rem;
  }
  .stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--st-brand-indigo), #818cf8) !important;
    color: #fff !important;
  }

  /* Metrics — softer cards */
  [data-testid="stMetricValue"] {
    font-variant-numeric: tabular-nums;
  }

  /* Dataframe / tables */
  [data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--st-brand-border);
  }

  /* Footer bar */
  .st-brand-footer {
    text-align: center;
    font-size: 0.78rem;
    color: var(--st-brand-muted);
    margin-top: 2.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--st-brand-border);
  }
  .st-brand-footer a {
    color: var(--st-brand-indigo);
    text-decoration: none;
    font-weight: 500;
  }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    """Top-of-page hero matching SimpleTest naming and links."""
    st.markdown(
        f"""
<div class="st-brand-hero">
  <div class="st-brand-hero-inner">
    <div class="st-brand-mark">ST</div>
    <div>
      <div class="st-brand-title">
        SimpleTest <span class="st-brand-pill">JIRA lab</span>
      </div>
      <p class="st-brand-sub">
        Pull and verify JIRA objects in line with the Salesforce Data Cloud
        <strong>JIRA Structured Connector</strong> catalog — build reusable test cases
        your team can run from this UI or check into source control.
      </p>
      <div class="st-brand-links">
        <a href="{BRAND_WEBSITE}" target="_blank" rel="noopener noreferrer">simpletest.ai</a>
        <a href="{BRAND_PLATFORM}" target="_blank" rel="noopener noreferrer">Platform</a>
        <a href="{BRAND_APP}" target="_blank" rel="noopener noreferrer">App</a>
      </div>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        f"""
<div class="st-brand-footer">
  Prototype for demonstrating JIRA object pulls · Learn more at
  <a href="{BRAND_WEBSITE}" target="_blank" rel="noopener noreferrer">SimpleTest</a>
</div>
        """,
        unsafe_allow_html=True,
    )
