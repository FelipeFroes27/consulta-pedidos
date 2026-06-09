import base64
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.display_mode import ativar_modo_exibicao, render_menu_lateral
from utils.sheets import carregar_dados


st.set_page_config(page_title="Recebimentos", layout="wide", initial_sidebar_state="expanded")
ativar_modo_exibicao("recebimentos")


MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Marco",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

CORES_GRUPO = ["#2563eb", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#06b6d4"]
PALETA_PLOTLY = ["#2563eb", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#06b6d4", "#64748b"]


st.markdown(
    """
    <style>
    header,
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
        border: 0 !important;
    }

    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    footer, #MainMenu {visibility: hidden;}
    [data-testid="stDecoration"] {display: none !important;}

    .stApp {
        background: #f7f9fc;
        color: #101828;
    }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 1540px;
        padding-top: 0.75rem;
        padding-bottom: 1.4rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 1.1rem;
    }

    div[data-testid="column"] {
        min-width: 0;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #dfe6ef;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 8px 24px rgba(16, 24, 40, .055);
        padding: 14px 16px 16px 16px;
    }

    div[data-testid="stRadio"] {
        margin-top: -4px;
        margin-bottom: 6px;
    }

    .page-head {
        margin-top: -1.2rem !important;
        margin-bottom: .35rem !important;
    }

    .page-title h1 {
        margin-top: 0 !important;
    }

    .page-title p {
        margin-top: 4px !important;
    }

    .month-title {
        min-height: 42px !important;
    }

    .kpi-card {
        min-height: 96px !important;
    }

    .next-card {
        margin-bottom: 8px !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: .75rem !important;
    }

    .page-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 18px;
        margin-bottom: .2rem;
    }

    .page-title h1 {
        margin: 0;
        color: #0f172a;
        font-size: 29px;
        line-height: 1.05;
        letter-spacing: 0;
        font-weight: 850;
    }

    .page-title p {
        margin: 6px 0 0 0;
        color: #667085;
        font-size: 14px;
    }

    .month-title {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 46px;
        width: 100%;
        border-radius: 8px;
        color: #2563eb;
        font-size: 29px;
        line-height: 1;
        font-weight: 850;
        letter-spacing: 0;
    }

    .nav-button .stButton > button,
    .refresh-button .stButton > button {
        height: 44px;
        border-radius: 8px;
        border: 1px solid #dce3ee;
        background: #ffffff;
        color: #2563eb;
        font-weight: 800;
        box-shadow: 0 6px 18px rgba(16, 24, 40, .05);
    }

    .nav-button .stButton > button:hover,
    .refresh-button .stButton > button:hover {
        border-color: #2563eb;
        background: #f8fbff;
    }

    .kpi-card {
        display: grid;
        grid-template-columns: 58px 1fr;
        gap: 16px;
        align-items: center;
        min-height: 108px;
        padding: 18px;
        border: 1px solid #dfe6ef;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 8px 24px rgba(16, 24, 40, .055);
    }

    .kpi-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 58px;
        height: 58px;
        border-radius: 999px;
        font-size: 25px;
        font-weight: 850;
    }

    .icon-blue {background: #eaf1ff; color: #2563eb;}
    .icon-green {background: #e8f8ef; color: #10a66a;}
    .icon-orange {background: #fff1df; color: #f97316;}
    .icon-purple {background: #f1e8ff; color: #8b5cf6;}

    .kpi-label {
        color: #475467;
        font-size: 14px;
        font-weight: 650;
    }

    .kpi-value {
        margin-top: 4px;
        color: #0f172a;
        font-size: 27px;
        line-height: 1;
        font-weight: 850;
    }

    .kpi-value.blue {color: #2563eb;}
    .kpi-value.green {color: #10a66a;}
    .kpi-value.orange {color: #f97316;}
    .kpi-value.purple {color: #8b5cf6;}

    .kpi-note {
        margin-top: 7px;
        color: #667085;
        font-size: 12px;
    }

    .panel {
        border: 1px solid #dfe6ef;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 8px 24px rgba(16, 24, 40, .055);
        padding: 16px;
    }

    .soft-panel {
        border: 1px solid #dfe6ef;
        border-radius: 8px;
        background:
            linear-gradient(135deg, rgba(37, 99, 235, .06), rgba(16, 185, 129, .05)),
            #ffffff;
        box-shadow: 0 8px 24px rgba(16, 24, 40, .055);
        padding: 16px;
    }

    .panel-title {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 0 0 12px 0;
        color: #101828;
        font-size: 16px;
        font-weight: 850;
    }

    .next-card {
        display: grid;
        grid-template-columns: 42px minmax(0, 1fr) 58px 58px;
        align-items: center;
        gap: 10px;
        padding: 9px 11px;
        margin-bottom: 8px;
        border-radius: 8px;
        border: 1px solid #dfe6ef;
        background: #f8fbff;
    }

    .next-card.today {background: #ecfdf5; border-color: #bbf7d0;}
    .next-card.soon {background: #eff6ff; border-color: #bfdbfe;}
    .next-card.attention {background: #fff7ed; border-color: #fed7aa;}
    .next-card.selected {outline: 2px solid #2563eb; background: #eff6ff;}

    .next-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 999px;
        background: #2563eb;
        color: white;
        font-size: 17px;
        font-weight: 850;
    }

    .next-card.today .next-icon {background: #16a34a;}
    .next-card.attention .next-icon {background: #f97316;}

    .next-when {
        color: #101828;
        font-size: 14px;
        line-height: 1.25;
        font-weight: 800;
    }

    .next-date {
        display: block;
        margin-top: 3px;
        color: #667085;
        font-size: 12px;
        font-weight: 600;
    }

    .next-extra {
        display: block;
        margin-top: 5px;
        color: #2563eb;
        font-size: 11px;
        font-weight: 800;
        max-width: 170px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .next-metric {
        text-align: right;
        min-width: 0;
    }

    .next-number {
        color: #2563eb;
        font-size: 16px;
        line-height: 1;
        font-weight: 850;
    }

    .next-label {
        margin-top: 4px;
        color: #667085;
        font-size: 11px;
    }

    .analysis-select {
        margin-bottom: 10px;
    }

    .analysis-select div[data-baseweb="select"] {
        font-size: 13px;
    }

    .next-action .stButton > button {
        min-height: 30px;
        margin-top: -4px;
        margin-bottom: 6px;
        border-radius: 8px;
        border: 1px solid #dbe7ff;
        background: #ffffff;
        color: #2563eb;
        font-size: 12px;
        font-weight: 800;
    }

    .next-action .stButton > button:hover {
        border-color: #2563eb;
        background: #eff6ff;
    }

    .mini-table {
        width: 100%;
        border-collapse: collapse;
        overflow: hidden;
        border-radius: 8px;
        font-size: 13px;
    }

    .mini-table th {
        padding: 10px 12px;
        border: 1px solid #e5eaf2;
        background: #f8fafc;
        color: #475467;
        text-align: left;
        font-weight: 800;
    }

    .mini-table td {
        padding: 10px 12px;
        border: 1px solid #e5eaf2;
        color: #344054;
        background: #ffffff;
    }

    .mini-table td.num,
    .mini-table th.num {
        text-align: center;
    }

    .tag {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 72px;
        max-width: 160px;
        padding: 4px 9px;
        border-radius: 6px;
        background: #eaf1ff;
        color: #2563eb;
        font-size: 11px;
        font-weight: 850;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .tag.green {background: #e8f8ef; color: #047857;}
    .tag.orange {background: #fff1df; color: #c2410c;}
    .tag.slate {background: #f1f5f9; color: #334155;}

    .insight-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
    }

    .insight {
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #dfe6ef;
        background: rgba(255, 255, 255, .74);
    }

    .insight-label {
        color: #667085;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
    }

    .insight-value {
        margin-top: 5px;
        color: #0f172a;
        font-size: 14px;
        font-weight: 850;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .progress-row {
        display: grid;
        grid-template-columns: minmax(96px, 1fr) 2.5fr 76px;
        align-items: center;
        gap: 12px;
        margin: 15px 0;
    }

    .progress-name {
        color: #101828;
        font-size: 13px;
        font-weight: 800;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .progress-track {
        height: 12px;
        border-radius: 999px;
        background: #eef2f7;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        border-radius: 999px;
    }

    .progress-value {
        color: #475467;
        font-size: 12px;
        text-align: right;
        white-space: nowrap;
    }

    .empty {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 110px;
        border: 1px dashed #d0d5dd;
        border-radius: 8px;
        color: #667085;
        background: #ffffff;
        text-align: center;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #dfe6ef;
        border-radius: 8px;
        overflow: hidden;
    }

    .analysis-chart-title {
        margin: 0 0 8px 0;
        color: #101828;
        font-size: 15px;
        line-height: 1.25;
        font-weight: 850;
    }

    .sidebar-logo {
        display: flex;
        justify-content: center;
        padding: 8px 0 18px 0;
    }

    div[data-testid="stExpander"] {
        margin-top: .35rem;
    }

    @media (max-width: 1000px) {
        .page-head {
            flex-direction: column;
        }

        .next-card {
            grid-template-columns: 38px 1fr;
        }

        .next-metric {
            text-align: left;
        }
    }

    .stApp,
    [data-testid="stAppViewContainer"] {
        background: #000000;
        color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background: #000000 !important;
        border-right: 1px solid #ffffff;
    }

    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
    }

    .sidebar-logo img,
    .page-logo {
        background: #ffffff;
        border: 2px solid #ffffff;
        border-radius: 8px;
        padding: 6px;
    }

    .page-title h1,
    .page-title p {
        color: #ffffff;
    }

    .page-logo {
        width: 126px;
        flex: 0 0 auto;
    }

    .month-title {
        color: #ffffff;
        border: 1px solid #ffffff;
    }

    .nav-button .stButton > button,
    .refresh-button .stButton > button,
    .next-action .stButton > button {
        border: 1px solid #000000;
        background: #ffffff;
        color: #000000;
        box-shadow: none;
    }

    .kpi-card,
    .panel,
    .soft-panel,
    div[data-testid="stVerticalBlockBorderWrapper"],
    .insight,
    .next-card,
    .mini-table th,
    .mini-table td,
    .empty {
        background: #ffffff;
        border-color: #000000;
        box-shadow: none;
    }

    .kpi-icon {
        background: #ffffff !important;
        border: 2px solid #000000;
        color: #000000 !important;
    }

    .next-card.today,
    .next-card.soon,
    .next-card.attention,
    .next-card.selected {
        background: #ffffff;
        border-color: #000000;
        outline-color: #000000;
    }

    .next-icon,
    .next-card.today .next-icon,
    .next-card.attention .next-icon {
        background: #ffffff;
        border: 2px solid #000000;
        color: #000000;
    }

    .kpi-value,
    .kpi-value.blue,
    .kpi-value.green,
    .kpi-value.orange,
    .kpi-value.purple,
    .next-number,
    .next-extra {
        color: #000000;
    }

    .tag,
    .tag.green,
    .tag.orange,
    .tag.slate {
        background: #ffffff;
        border: 1px solid #000000;
        color: #000000;
    }

    .stApp,
    [data-testid="stAppViewContainer"] {
        background: #ffffff;
        color: #000000;
    }

    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #000000;
    }

    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    label {
        color: #000000 !important;
    }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 1540px;
        padding-top: 1.25rem;
        padding-bottom: 1.25rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 1rem;
    }

    .page-head {
        align-items: flex-start;
        gap: 20px;
        margin-bottom: 1.25rem;
    }

    .page-title h1,
    .page-title p,
    .month-title {
        color: #000000;
    }

    .page-logos {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 0 0 auto;
    }

    .page-logos img {
        max-height: 30px;
        max-width: 104px;
        object-fit: contain;
    }

    .sidebar-logo img {
        border: 0;
        padding: 0;
        max-height: 24px;
        width: auto;
    }

    .month-title,
    .kpi-card,
    .panel,
    .soft-panel,
    div[data-testid="stVerticalBlockBorderWrapper"],
    .insight,
    .mini-table th,
    .mini-table td,
    div[data-testid="stDataFrame"] {
        border: 2px solid #000000;
        border-radius: 12px;
        box-shadow: none;
    }

    .kpi-card,
    .panel,
    .soft-panel,
    .insight,
    .mini-table th,
    .mini-table td,
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
    }

    .kpi-icon {
        background: #ffffff !important;
        border: 2px solid #000000;
        color: #000000 !important;
    }

    .nav-button .stButton > button,
    .refresh-button .stButton > button {
        border: 2px solid #000000;
        background: #ffffff;
        color: #000000;
        border-radius: 7px;
        box-shadow: none;
    }

    .next-card {
        border-radius: 12px;
    }

    .next-card.today {background: #ecfdf5; border-color: #22c55e;}
    .next-card.soon {background: #eff6ff; border-color: #60a5fa;}
    .next-card.attention {background: #fff7ed; border-color: #fb923c;}
    .next-card.selected {outline: 2px solid #000000;}
    .next-icon {background: #2563eb; border: 2px solid #000000; color: #ffffff;}
    .next-card.today .next-icon {background: #16a34a;}
    .next-card.attention .next-icon {background: #f97316;}

    .next-panel {
        border: 2px solid #000000;
        border-radius: 12px;
        background: #ffffff;
        padding: 14px;
        min-height: 100%;
    }

    .next-panel .panel-title {
        margin-bottom: 12px;
    }

    .analysis-select {
        margin: 0 0 12px 0;
    }

    .analysis-select div[data-baseweb="select"] > div {
        min-height: 42px;
        border: 2px solid #000000;
        border-radius: 7px;
        background: #ffffff;
    }

    .next-card {
        grid-template-columns: 38px minmax(0, 1fr) 50px 50px;
        gap: 10px;
        min-height: 76px;
        padding: 10px;
        margin-bottom: 10px;
        border-width: 2px;
        box-shadow: none;
    }

    .next-card.danger {
        background: #fff1f2;
        border-color: #000000;
    }

    .next-card.warning {
        background: #fffbeb;
        border-color: #000000;
    }

    .next-card.soon {
        background: #eff6ff;
        border-color: #000000;
    }

    .next-card.safe {
        background: #ecfdf5;
        border-color: #000000;
    }

    .next-card.selected {
        outline: 2px solid #000000;
        outline-offset: 1px;
    }

    .next-card.danger .next-icon {background: #ef4444;}
    .next-card.warning .next-icon {background: #f59e0b;}
    .next-card.soon .next-icon {background: #3b82f6;}
    .next-card.safe .next-icon {background: #22c55e;}

    .next-icon {
        width: 32px;
        height: 32px;
        border: 2px solid #000000;
        color: #ffffff;
        font-size: 15px;
    }

    .next-when {
        font-size: 13px;
    }

    .next-date {
        margin-top: 2px;
    }

    .next-extra {
        margin-top: 4px;
        max-width: 150px;
    }

    .next-number {
        font-size: 15px;
    }

    .next-label {
        font-size: 10px;
    }

    .kpi-card,
    .panel,
    .soft-panel,
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 14px;
    }

    .kpi-card {
        min-height: 96px;
    }

    .insight-grid {
        gap: 12px;
    }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        padding-top: .25rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 1.25rem !important;
    }

    div[data-testid="column"] {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    .kpi-card,
    .panel,
    .soft-panel,
    div[data-testid="stVerticalBlockBorderWrapper"] {
        margin: 0 !important;
    }

    .kpi-card {
        min-height: 110px;
    }

    .month-title {
        min-height: 48px;
    }

    .next-icon,
    .next-card.danger .next-icon,
    .next-card.warning .next-icon,
    .next-card.soon .next-icon,
    .next-card.safe .next-icon,
    .next-card.today .next-icon,
    .next-card.attention .next-icon {
        border: 2px solid #000000 !important;
    }

    .next-card {
        margin-bottom: 12px;
    }

    .next-card:last-child {
        margin-bottom: 0;
    }

    .next-card,
    .next-card.danger,
    .next-card.warning,
    .next-card.soon,
    .next-card.safe,
    .next-card.selected {
        border: 2px solid #000000 !important;
    }

    .next-card.danger,
    .next-card.warning,
    .next-card.soon,
    .next-card.safe {
        box-shadow: none !important;
    }

    div[data-baseweb="select"] > div,
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        border: 2px solid #000000 !important;
        border-radius: 7px !important;
        background: #ffffff !important;
        box-shadow: none !important;
        outline: none !important;
    }

    div[data-baseweb="select"] svg {
        color: #000000 !important;
    }

    div[data-testid="stExpander"] {
        border: 2px solid #000000 !important;
        border-radius: 12px !important;
        background: #ffffff !important;
        box-shadow: none !important;
        overflow: hidden !important;
    }

    div[data-testid="stExpander"] details,
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] [role="button"] {
        border-color: #000000 !important;
        box-shadow: none !important;
        outline: none !important;
    }

    div[data-testid="stExpander"] summary {
        background: #ffffff !important;
    }

    div[data-testid="stDataFrame"] {
        border: 2px solid #000000 !important;
        border-radius: 12px !important;
        box-shadow: none !important;
    }

    .next-icon,
    .kpi-icon {
        box-sizing: border-box !important;
        border: 2px solid #000000 !important;
    }

    .stButton > button,
    button[kind],
    div[data-testid="stBaseButton-secondary"] button,
    div[data-testid="stBaseButton-primary"] button {
        border: 2px solid #000000 !important;
        border-radius: 7px !important;
        box-shadow: none !important;
        outline: none !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stExpander"],
    div[data-testid="stDataFrame"],
    div[data-testid="stSelectbox"],
    div[data-testid="stDateInput"],
    div[data-testid="stTabs"] button,
    div[data-testid="stTabs"] [role="tab"] {
        border-color: #000000 !important;
        box-shadow: none !important;
        outline-color: #000000 !important;
    }

    div[data-testid="stExpander"] > details {
        border: 0 !important;
    }

    div[data-testid="stExpander"] summary {
        border-bottom: 2px solid #000000 !important;
    }

    div[data-testid="stDataFrame"] div,
    div[data-testid="stDataFrame"] canvas {
        outline-color: #000000 !important;
    }

    .tag,
    .tag.green,
    .tag.orange,
    .tag.slate,
    .progress-track {
        border: 1px solid #000000 !important;
    }

    .analysis-select div[data-baseweb="select"] > div,
    .next-panel-title + div[data-baseweb="select"] > div {
        border: 2px solid #000000 !important;
        background: #ffffff !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.next-panel-title) {
        border: 2px solid #000000 !important;
        border-radius: 12px !important;
        box-shadow: none !important;
    }

    .nav-button .stButton > button,
    .refresh-button .stButton > button,
    .stButton > button,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-primary"],
    button[kind="secondary"],
    button[kind="primary"] {
        border: 2px solid #000000 !important;
        border-color: #000000 !important;
        border-radius: 7px !important;
        background: #ffffff !important;
        color: #000000 !important;
        box-shadow: none !important;
        outline: none !important;
    }

    .nav-button .stButton > button:disabled,
    .refresh-button .stButton > button:disabled,
    .stButton > button:disabled {
        border: 2px solid #000000 !important;
        border-color: #000000 !important;
        color: #777777 !important;
        opacity: .65 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.next-panel-title) {
        border: 2px solid #000000 !important;
        border-radius: 12px !important;
        padding: 16px !important;
        background: #ffffff !important;
    }

    .next-panel-title {
        margin: 0 0 14px 0 !important;
        font-size: 16px !important;
    }

    .next-card,
    .next-card.danger,
    .next-card.warning,
    .next-card.soon,
    .next-card.safe,
    .next-card.selected {
        grid-template-columns: 36px minmax(0, 1fr) 48px 56px !important;
        min-height: 82px !important;
        padding: 11px 12px !important;
        margin: 0 0 10px 0 !important;
        border: 2px solid #000000 !important;
        border-radius: 10px !important;
        background: #ffffff !important;
        outline: none !important;
    }

    .next-card.selected {
        box-shadow: inset 0 0 0 2px #000000 !important;
    }

    .next-card.danger {box-shadow: inset 5px 0 0 #ef4444 !important;}
    .next-card.warning {box-shadow: inset 5px 0 0 #f59e0b !important;}
    .next-card.soon {box-shadow: inset 5px 0 0 #3b82f6 !important;}
    .next-card.safe {box-shadow: inset 5px 0 0 #22c55e !important;}

    .next-card.danger .next-icon {background: #ef4444 !important;}
    .next-card.warning .next-icon {background: #f59e0b !important;}
    .next-card.soon .next-icon {background: #3b82f6 !important;}
    .next-card.safe .next-icon {background: #22c55e !important;}

    .next-icon {
        width: 30px !important;
        height: 30px !important;
        border: 2px solid #000000 !important;
        color: #ffffff !important;
        font-size: 13px !important;
    }

    .next-when {
        font-size: 13px !important;
        line-height: 1.15 !important;
    }

    .next-date,
    .next-label {
        font-size: 10px !important;
    }

    .next-extra {
        max-width: 135px !important;
        font-size: 10px !important;
    }

    .next-number {
        font-size: 14px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.analysis-chart-title) {
        border: 2px solid #000000 !important;
        border-radius: 12px !important;
        padding: 14px !important;
        box-shadow: none !important;
    }

    .analysis-chart-title {
        margin-bottom: 8px !important;
    }

    /* Compactacao final para telas grandes */
    .block-container,
    [data-testid="stMainBlockContainer"] {
        padding-top: .25rem !important;
        padding-bottom: .5rem !important;
    }

    .page-head {
        margin-top: 1.1rem !important;
        margin-bottom: .3rem !important;
        min-height: 64px !important;
    }

    .page-title h1 {
        font-size: 27px !important;
        line-height: 1 !important;
        margin: 0 !important;
    }

    .page-title p {
        margin: 3px 0 0 0 !important;
        font-size: 13px !important;
    }

    .page-logos {
        margin-top: 0 !important;
    }

    .page-logos img {
        max-height: 34px !important;
    }

    div[data-testid="stVerticalBlock"] {
        gap: .45rem !important;
    }

    .month-title {
        min-height: 38px !important;
        font-size: 26px !important;
    }

    .nav-button .stButton > button,
    .refresh-button .stButton > button {
        min-height: 38px !important;
    }

    .kpi-card {
        min-height: 88px !important;
        padding: 10px 14px !important;
    }

    .kpi-icon {
        width: 52px !important;
        height: 52px !important;
    }

    .kpi-value {
        font-size: 24px !important;
        line-height: 1.05 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.next-panel-title),
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.analysis-chart-title) {
        padding: 12px !important;
    }

    .next-panel-title {
        margin-bottom: 8px !important;
    }

    .next-card,
    .next-card.danger,
    .next-card.warning,
    .next-card.soon,
    .next-card.safe,
    .next-card.selected {
        min-height: 72px !important;
        padding: 8px 10px !important;
        margin-bottom: 7px !important;
    }

    .insight-grid[style] {
        margin-bottom: 6px !important;
    }

    .insight {
        min-height: 78px !important;
        padding: 10px 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

render_menu_lateral()

with st.sidebar:
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    st.image("Logo Branco.bmp", width=72)
    st.image("logo preto goper.png", width=32)
    st.markdown("</div>", unsafe_allow_html=True)
    st.page_link("app.py", label="Início")
    st.page_link("pages/Consulta_Pedidos.py", label="Consulta de Pedidos")
    st.page_link("pages/Cronograma.py", label="Recebimentos")
    st.page_link("pages/Embarques.py", label="Embarques")


def texto(serie):
    return serie.fillna("").astype(str).str.strip()


def preparar_dados(df_original):
    df = df_original.copy()
    obrigatorias = ["Data Entrega", "Numero do Pedido", "Subgrupo", "Grupo"]
    faltantes = [col for col in obrigatorias if col not in df.columns]

    if faltantes:
        st.error("A aba Pedidos precisa conter estas colunas: " + ", ".join(obrigatorias))
        st.stop()

    df["Data Entrega"] = pd.to_datetime(df["Data Entrega"], errors="coerce", dayfirst=True)
    df = df[df["Data Entrega"].notna()].copy()

    if df.empty:
        return df

    df["Numero do Pedido"] = texto(df["Numero do Pedido"])
    df["Subgrupo"] = texto(df["Subgrupo"]).replace("", "Não informado")
    df["Grupo"] = texto(df["Grupo"]).replace("", "Não informado")
    df["Data Recebimento"] = df["Data Entrega"].dt.date

    if "Tipo" in df.columns:
        df["Tipo"] = texto(df["Tipo"]).replace("", "Não informado")
    else:
        df["Tipo"] = "Não informado"

    if "Categoria" in df.columns:
        df["Categoria"] = texto(df["Categoria"]).replace("", "Não informado")
    else:
        df["Categoria"] = "Não informado"

    if "Qtde" in df.columns:
        df["Qtde"] = pd.to_numeric(df["Qtde"], errors="coerce").fillna(0)
    else:
        df["Qtde"] = 1

    for coluna in ["Codigo", "Descricao", "Marca"]:
        if coluna in df.columns:
            df[coluna] = texto(df[coluna])

    return df


def mes_formatado(periodo):
    return f"{MESES_PT[periodo.month]} {periodo.year}"


def numero(valor):
    return f"{int(valor):,}".replace(",", ".")


def render_kpi(titulo, valor, nota, icone, cor):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon icon-{cor}">{icone}</div>
            <div>
                <div class="kpi-label">{escape(titulo)}</div>
                <div class="kpi-value {cor}">{numero(valor)}</div>
                <div class="kpi-note">{escape(nota)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def resumo_por_data(df):
    return (
        df.groupby("Data Recebimento")
        .agg(
            Pedidos=("Numero do Pedido", "nunique"),
            Itens=("Qtde", "sum"),
            Linhas=("Numero do Pedido", "size"),
            Fornecedores=("Subgrupo", "nunique"),
            Principal_Fornecedor=("Subgrupo", lambda s: s.value_counts().index[0] if not s.empty else ""),
            Grupo_Principal=("Grupo", lambda s: s.value_counts().index[0] if not s.empty else ""),
            Tipo_Principal=("Tipo", lambda s: s.value_counts().index[0] if not s.empty else ""),
        )
        .reset_index()
        .sort_values("Data Recebimento")
    )


def label_prazo(data_recebimento):
    hoje = pd.Timestamp.today().normalize().date()
    dias = (data_recebimento - hoje).days

    if dias == 0:
        return "Hoje", "danger"
    if dias == 1:
        return "Amanhã", "danger"
    if dias < 5:
        return f"Em {dias} dias", "danger"
    if dias <= 10:
        return f"Em {dias} dias", "warning"
    if dias < 15:
        return f"Em {dias} dias", "soon"
    return f"Em {dias} dias", "safe"


def proximas_datas(df, limite=5):
    hoje = pd.Timestamp.today().normalize().date()
    return resumo_por_data(df[df["Data Recebimento"] >= hoje]).head(limite)


def render_proximas_entregas(proximas):
    if "cronograma_data_alerta" not in st.session_state and not proximas.empty:
        st.session_state.cronograma_data_alerta = proximas.iloc[0]["Data Recebimento"].strftime("%Y-%m-%d")

    st.markdown('<div class="panel-title next-panel-title">Próximas entregas</div>', unsafe_allow_html=True)

    if proximas.empty:
        st.markdown('<div class="empty">Nenhum recebimento futuro cadastrado.</div>', unsafe_allow_html=True)
        return

    opcoes = {
        f"{label_prazo(linha['Data Recebimento'])[0]} - {linha['Data Recebimento'].strftime('%d/%m/%Y')}": linha["Data Recebimento"].strftime("%Y-%m-%d")
        for _, linha in proximas.iterrows()
    }
    valores = list(opcoes.values())
    valor_atual = st.session_state.get("cronograma_data_alerta", valores[0])
    indice_atual = valores.index(valor_atual) if valor_atual in valores else 0

    st.markdown('<div class="analysis-select">', unsafe_allow_html=True)
    escolha = st.selectbox(
        "Entrega analisada",
        list(opcoes.keys()),
        index=indice_atual,
        label_visibility="collapsed",
    )
    st.session_state.cronograma_data_alerta = opcoes[escolha]
    st.markdown("</div>", unsafe_allow_html=True)

    for _, linha in proximas.iterrows():
        data_recebimento = linha["Data Recebimento"]
        quando, classe = label_prazo(data_recebimento)
        selecionado = "selected" if data_recebimento.strftime("%Y-%m-%d") == st.session_state.cronograma_data_alerta else ""

        st.markdown(
            f"""
            <div class="next-card {classe} {selecionado}">
                <div class="next-icon" style="border:2px solid #000000;">▦</div>
                <div>
                    <div class="next-when">{escape(quando)}</div>
                    <span class="next-date">{data_recebimento.strftime("%d/%m/%Y")}</span>
                    <span class="next-extra">{escape(str(linha["Grupo_Principal"]))} | {escape(str(linha["Tipo_Principal"]))}</span>
                </div>
                <div class="next-metric">
                    <div class="next-number">{numero(linha["Pedidos"])}</div>
                    <div class="next-label">Pedidos</div>
                </div>
                <div class="next-metric">
                    <div class="next-number">{numero(linha["Itens"])}</div>
                    <div class="next-label">Itens</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tabela_mes(resumo):
    linhas = []
    for _, linha in resumo.head(8).iterrows():
        linhas.append(
            "<tr>"
            f"<td>{linha['Data Recebimento'].strftime('%d/%m/%Y')}</td>"
            f"<td class='num'>{numero(linha['Pedidos'])}</td>"
            f"<td class='num'>{numero(linha['Itens'])}</td>"
            f"<td class='num'>{numero(linha['Fornecedores'])}</td>"
            f"<td><span class='tag' title='{escape(str(linha['Principal_Fornecedor']))}'>{escape(str(linha['Principal_Fornecedor']))}</span></td>"
            f"<td><span class='tag green' title='{escape(str(linha['Grupo_Principal']))}'>{escape(str(linha['Grupo_Principal']))}</span></td>"
            f"<td><span class='tag orange' title='{escape(str(linha['Tipo_Principal']))}'>{escape(str(linha['Tipo_Principal']))}</span></td>"
            "</tr>"
        )

    if not linhas:
        return '<div class="empty">Sem recebimentos neste mês.</div>'

    return (
        "<table class='mini-table'>"
        "<thead>"
        "<tr>"
        "<th>Data</th>"
        "<th class='num'>Pedidos</th>"
        "<th class='num'>Itens</th>"
        "<th class='num'>Fornecedores</th>"
        "<th>Fornecedor principal</th>"
        "<th>Grupo principal</th>"
        "<th>Tipo principal</th>"
        "</tr>"
        "</thead>"
        "<tbody>"
        + "".join(linhas)
        + "</tbody></table>"
    )


def render_ranking(titulo, df_ranking, coluna_nome, sufixo):
    st.markdown(f'<div class="panel"><div class="panel-title">{escape(titulo)}</div>', unsafe_allow_html=True)

    if df_ranking.empty:
        st.markdown('<div class="empty">Sem dados para exibir.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    maximo = max(float(df_ranking["Pedidos"].max()), 1)

    for indice, (_, linha) in enumerate(df_ranking.iterrows()):
        largura = int((float(linha["Pedidos"]) / maximo) * 100)
        cor = CORES_GRUPO[indice % len(CORES_GRUPO)]
        nome = escape(str(linha[coluna_nome]))

        st.markdown(
            f"""
            <div class="progress-row">
                <div class="progress-name" title="{nome}">{nome}</div>
                <div class="progress-track">
                    <div class="progress-fill" style="width:{largura}%; background:{cor};"></div>
                </div>
                <div class="progress-value">{numero(linha["Pedidos"])} {sufixo}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def valor_top(df, coluna):
    if df.empty or coluna not in df.columns:
        return "Sem dados", 0

    ranking = df.groupby(coluna).agg(Pedidos=("Numero do Pedido", "nunique")).reset_index()
    if ranking.empty:
        return "Sem dados", 0

    linha = ranking.sort_values("Pedidos", ascending=False).iloc[0]
    return str(linha[coluna]), int(linha["Pedidos"])


def render_leitura_operacional(df_mes):
    grupo, pedidos_grupo = valor_top(df_mes, "Grupo")
    tipo, pedidos_tipo = valor_top(df_mes, "Tipo")
    fornecedor, pedidos_fornecedor = valor_top(df_mes, "Subgrupo")

    st.markdown(
        f"""
        <div class="soft-panel">
            <div class="panel-title">Leitura operacional do mês</div>
            <div class="insight-grid">
                <div class="insight">
                    <div class="insight-label">Grupo dominante</div>
                    <div class="insight-value" title="{escape(grupo)}">{escape(grupo)}</div>
                    <div class="kpi-note">{numero(pedidos_grupo)} pedidos</div>
                </div>
                <div class="insight">
                    <div class="insight-label">Tipo dominante</div>
                    <div class="insight-value" title="{escape(tipo)}">{escape(tipo)}</div>
                    <div class="kpi-note">{numero(pedidos_tipo)} pedidos</div>
                </div>
                <div class="insight">
                    <div class="insight-label">Fornecedor mais recorrente</div>
                    <div class="insight-value" title="{escape(fornecedor)}">{escape(fornecedor)}</div>
                    <div class="kpi-note">{numero(pedidos_fornecedor)} pedidos</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analise_entrega(df, data_alerta):
    if data_alerta is None:
        st.markdown('<div class="empty">Selecione uma próxima entrega para analisar.</div>', unsafe_allow_html=True)
        return

    df_alerta = df[df["Data Recebimento"] == data_alerta].copy()

    if df_alerta.empty:
        st.markdown('<div class="empty">Não há itens para a data selecionada.</div>', unsafe_allow_html=True)
        return

    pedidos = df_alerta["Numero do Pedido"].nunique()
    itens = df_alerta["Qtde"].sum()
    fornecedores = df_alerta["Subgrupo"].nunique()
    lista_fornecedores = sorted(df_alerta["Subgrupo"].dropna().astype(str).unique())
    fornecedores_resumo = ", ".join(lista_fornecedores[:3])
    if len(lista_fornecedores) > 3:
        fornecedores_resumo += f" +{len(lista_fornecedores) - 3}"

    st.markdown(
        f"""
        <div class="panel-title">Análise da entrega de {data_alerta.strftime("%d/%m/%Y")}</div>
        <div class="insight-grid" style="margin-bottom: 12px;">
            <div class="insight">
                <div class="insight-label">Pedidos</div>
                <div class="insight-value">{numero(pedidos)}</div>
            </div>
            <div class="insight">
                <div class="insight-label">Itens</div>
                <div class="insight-value">{numero(itens)}</div>
            </div>
            <div class="insight">
                <div class="insight-label">Fornecedores</div>
                <div class="insight-value" title="{escape(', '.join(lista_fornecedores))}">{escape(fornecedores_resumo)}</div>
                <div class="kpi-note">{numero(fornecedores)} fornecedores</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    grupo, categoria = st.columns(2)

    with grupo:
        with st.container(border=True):
            st.markdown('<div class="analysis-chart-title">Itens por Grupo</div>', unsafe_allow_html=True)
            por_grupo = (
                df_alerta.groupby("Grupo")
                .agg(Itens=("Qtde", "sum"), Pedidos=("Numero do Pedido", "nunique"))
                .reset_index()
                .sort_values("Itens", ascending=False)
            )
            fig_grupo = px.pie(
                por_grupo,
                names="Grupo",
                values="Itens",
                hole=.55,
                color_discrete_sequence=PALETA_PLOTLY,
            )
            fig_grupo = ajustar_pizza(fig_grupo)
            fig_grupo.update_traces(hovertemplate="<b>%{label}</b><br>Itens: %{value}<extra></extra>")
            st.plotly_chart(
                estilizar_grafico(fig_grupo, altura=430, legenda=True),
                use_container_width=True,
                config={"displayModeBar": False},
            )

    with categoria:
        with st.container(border=True):
            st.markdown('<div class="analysis-chart-title">Itens por Categoria</div>', unsafe_allow_html=True)
            por_categoria = (
                df_alerta.groupby("Categoria")
                .agg(Itens=("Qtde", "sum"), Pedidos=("Numero do Pedido", "nunique"))
                .reset_index()
                .sort_values("Itens", ascending=False)
            )
            fig_categoria = px.pie(
                por_categoria,
                names="Categoria",
                values="Itens",
                hole=.55,
                color_discrete_sequence=["#f97316", "#2563eb", "#10b981", "#8b5cf6", "#64748b"],
            )
            fig_categoria = ajustar_pizza(fig_categoria)
            fig_categoria.update_traces(hovertemplate="<b>%{label}</b><br>Itens: %{value}<extra></extra>")
            st.plotly_chart(
                estilizar_grafico(fig_categoria, altura=430, legenda=True),
                use_container_width=True,
                config={"displayModeBar": False},
            )


def ajustar_pizza(fig):
    fig.update_traces(
        textinfo="value",
        texttemplate="%{value}",
        textposition="inside",
        textfont=dict(color="#000000", size=12),
        marker=dict(line=dict(color="#000000", width=2)),
        domain=dict(x=[0.08, 0.92], y=[0.28, 0.98]),
    )
    return fig


def encurtar_legenda(texto, limite=22):
    texto = str(texto)
    return texto if len(texto) <= limite else texto[: limite - 3] + "..."


def ajustar_legenda_pizza(fig):
    for trace in fig.data:
        if hasattr(trace, "labels") and trace.labels is not None:
            trace.customdata = list(trace.labels)
            trace.labels = [encurtar_legenda(label) for label in trace.labels]
            trace.hovertemplate = "<b>%{customdata}</b><br>Itens: %{value}<extra></extra>"
    return fig


def estilizar_grafico(fig, altura=282, legenda=False):
    if legenda:
        fig = ajustar_legenda_pizza(fig)

    fig.update_layout(
        height=altura,
        margin=dict(l=8, r=8, t=4, b=128),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Arial", size=11, color="#475467"),
        showlegend=legenda,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(size=10, color="#101828"),
            itemwidth=88,
            traceorder="normal",
            bgcolor="#ffffff",
            bordercolor="#000000",
            borderwidth=0,
            itemsizing="constant",
        ),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e5eaf2", tickfont=dict(color="#667085"))
    fig.update_yaxes(gridcolor="#e9eef5", linecolor="#e5eaf2", tickfont=dict(color="#667085"))
    return fig


df = preparar_dados(carregar_dados())
logo_branco = base64.b64encode(Path("Logo Branco.bmp").read_bytes()).decode("utf-8")
logo_preto = base64.b64encode(Path("logo preto goper.png").read_bytes()).decode("utf-8")

st.markdown(
    f"""
    <div class="page-head">
        <div class="page-title">
            <h1>Recebimentos</h1>
            <p>Acompanhe os recebimentos previstos por data, fornecedor e grupo operacional.</p>
        </div>
        <div class="page-logos">
            <img src="data:image/bmp;base64,{logo_branco}" alt="Trendx">
            <img src="data:image/png;base64,{logo_preto}" alt="Goper">
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df.empty:
    st.markdown('<div class="empty">Não há datas válidas na coluna Data Entrega da aba Pedidos.</div>', unsafe_allow_html=True)
    st.stop()

meses = sorted(df["Data Entrega"].dt.to_period("M").unique())
mes_atual = pd.Timestamp.today().to_period("M")
idx_padrao = meses.index(mes_atual) if mes_atual in meses else len(meses) - 1

if "cronograma_mes_idx" not in st.session_state:
    st.session_state.cronograma_mes_idx = idx_padrao

mes_selecionado = meses[st.session_state.cronograma_mes_idx]

nav_1, nav_2, nav_3, nav_4 = st.columns([.55, 3.1, .55, .8])

with nav_1:
    st.markdown('<div class="nav-button">', unsafe_allow_html=True)
    if st.button("‹", use_container_width=True, disabled=st.session_state.cronograma_mes_idx <= 0):
        st.session_state.cronograma_mes_idx -= 1
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with nav_2:
    st.markdown(f'<div class="month-title">{escape(mes_formatado(mes_selecionado))}</div>', unsafe_allow_html=True)

with nav_3:
    st.markdown('<div class="nav-button">', unsafe_allow_html=True)
    if st.button("›", use_container_width=True, disabled=st.session_state.cronograma_mes_idx >= len(meses) - 1):
        st.session_state.cronograma_mes_idx += 1
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with nav_4:
    st.markdown('<div class="refresh-button">', unsafe_allow_html=True)
    if st.button("Atualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

df_mes = df[df["Data Entrega"].dt.to_period("M") == mes_selecionado].copy()

k1, k2, k3, k4 = st.columns(4)

with k1:
    render_kpi("Pedidos do Mês", df_mes["Numero do Pedido"].nunique(), "Total de pedidos", "▤", "blue")
with k2:
    render_kpi("Itens do Mês", df_mes["Qtde"].sum(), "Soma das quantidades", "□", "green")
with k3:
    render_kpi("Fornecedores", df_mes["Subgrupo"].nunique(), "Fornecedores diferentes", "●", "orange")
with k4:
    render_kpi("Dias com Entrega", df_mes["Data Recebimento"].nunique(), "Dias no mês", "▣", "purple")

proximas = proximas_datas(df)

col_proximas, col_grafico = st.columns([1.05, 2.55], gap="medium")

with col_proximas:
    with st.container(border=True):
        render_proximas_entregas(proximas)

with col_grafico:
    with st.container(border=True):
        data_alerta = None
        if "cronograma_data_alerta" in st.session_state:
            data_alerta = pd.to_datetime(st.session_state.cronograma_data_alerta).date()
        render_analise_entrega(df, data_alerta)

if "cronograma_data_alerta" in st.session_state:
    data_detalhe = pd.to_datetime(st.session_state.cronograma_data_alerta).date()
    df_detalhe = df[df["Data Recebimento"] == data_detalhe].copy()
    titulo_detalhe = f"Recebimentos detalhados de {data_detalhe.strftime('%d/%m/%Y')}"
else:
    df_detalhe = df_mes.copy()
    titulo_detalhe = "Recebimentos detalhados"

col_rank, col_detalhe = st.columns([1, 1.65], gap="medium")

with col_rank:
    aba_fornecedor, aba_grupo, aba_tipo = st.tabs(["Fornecedores", "Grupos", "Tipos"])

    with aba_fornecedor:
        ranking_fornecedor = (
            df_mes.groupby("Subgrupo")
            .agg(Pedidos=("Numero do Pedido", "nunique"), Itens=("Qtde", "sum"))
            .reset_index()
            .sort_values("Pedidos", ascending=False)
            .head(6)
        )
        render_ranking("Top fornecedores do mês", ranking_fornecedor, "Subgrupo", "ped.")

    with aba_grupo:
        ranking_grupo = (
            df_mes.groupby("Grupo")
            .agg(Pedidos=("Numero do Pedido", "nunique"), Itens=("Qtde", "sum"))
            .reset_index()
            .sort_values("Pedidos", ascending=False)
            .head(6)
        )
        render_ranking("Distribuição por grupo", ranking_grupo, "Grupo", "ped.")

    with aba_tipo:
        ranking_tipo = (
            df_mes.groupby("Tipo")
            .agg(Pedidos=("Numero do Pedido", "nunique"), Itens=("Qtde", "sum"))
            .reset_index()
            .sort_values("Pedidos", ascending=False)
            .head(6)
        )
        render_ranking("Distribuição por tipo", ranking_tipo, "Tipo", "ped.")

with col_detalhe:
    fornecedores_detalhe = ["Todos"] + sorted(df_detalhe["Subgrupo"].dropna().astype(str).unique())
    titulo_col, filtro_col = st.columns([1.45, 1])
    with filtro_col:
        fornecedor_filtro = st.selectbox(
            "Fornecedor",
            fornecedores_detalhe,
            key="recebimento_fornecedor_select",
        )

    if fornecedor_filtro != "Todos":
        df_detalhe = df_detalhe[df_detalhe["Subgrupo"] == fornecedor_filtro].copy()
        titulo_detalhe += f" - {fornecedor_filtro}"

    colunas = [
        "Numero do Pedido",
        "Data Entrega",
        "Subgrupo",
        "Grupo",
        "Codigo",
        "Descricao",
        "Qtde",
    ]
    colunas = [col for col in colunas if col in df_detalhe.columns]
    df_detalhe = df_detalhe[colunas].copy()

    for coluna_texto in ["Numero do Pedido", "Codigo"]:
        if coluna_texto in df_detalhe.columns:
            df_detalhe[coluna_texto] = df_detalhe[coluna_texto].fillna("").astype(str).str.strip()

    if "Data Entrega" in df_detalhe.columns:
        df_detalhe["Data Entrega"] = df_detalhe["Data Entrega"].dt.strftime("%d/%m/%Y")

    df_detalhe = df_detalhe.rename(
        columns={
            "Numero do Pedido": "Pedido",
            "Data Entrega": "Data de Entrega",
            "Subgrupo": "Fornecedor",
            "Descricao": "Descrição",
            "Codigo": "Código",
            "Qtde": "Quantidade",
        }
    )

    for coluna_texto in ["Pedido", "Código"]:
        if coluna_texto in df_detalhe.columns:
            df_detalhe[coluna_texto] = df_detalhe[coluna_texto].fillna("").astype("string")

    with titulo_col:
        st.markdown(f'<div class="panel"><div class="panel-title">{escape(titulo_detalhe)}</div></div>', unsafe_allow_html=True)
    st.dataframe(
        df_detalhe,
        use_container_width=True,
        hide_index=True,
        height=360,
        column_config={
            "Pedido": st.column_config.TextColumn("Pedido"),
            "Código": st.column_config.TextColumn("Código"),
        },
    )
