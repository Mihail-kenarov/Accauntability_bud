import asyncio
import html
import json
import threading
from datetime import date, datetime
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage
from markdown_it import MarkdownIt

from agent.agent import build_agent
from agent.calendar_mcp import build_calendar_mcp_client
from agent.fact_extractor import extract_and_store_facts
from agent.prompts import build_system_prompt
from agent.tools.chroma_tools import (
    retrieve_past_logs,
    retrieve_user_facts,
    save_conversation_log,
    store_user_fact,
)
from agent.tools.sqlite_tools import (
    get_daily_tasks,
    get_daily_plan,
    get_habit_streaks,
    init_db,
    log_habit,
    save_daily_plan,
    save_daily_tasks,
    set_daily_subtask_completion,
    set_daily_task_completion,
    update_habit_streaks,
)
from mcp_servers.google_calendar_server import _list_calendar_events


load_dotenv(override=True)
init_db()

st.set_page_config(
    page_title="Accountability Bud",
    page_icon="AB",
    layout="wide",
    initial_sidebar_state="expanded",
)


CSS = """
<style>
:root {
    --surface: oklch(98.2% 0.006 145);
    --panel: oklch(99.1% 0.004 145);
    --panel-strong: oklch(95.8% 0.012 145);
    --line: oklch(89.5% 0.014 145);
    --text: oklch(25% 0.025 150);
    --muted: oklch(52% 0.025 150);
    --soft: oklch(70% 0.026 150);
    --accent: oklch(54% 0.105 150);
    --accent-soft: oklch(93.5% 0.035 150);
    --warning-soft: oklch(94.5% 0.035 85);
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
}

html,
body,
[data-testid="stAppViewContainer"] {
    min-height: 100vh;
    background: var(--surface);
}

.stApp {
    min-height: 100vh;
    background:
        linear-gradient(180deg, var(--surface) 0%, oklch(96.8% 0.008 145) 100%);
    color: var(--text);
}

.block-container {
    max-width: 1540px;
    padding-top: 3.7rem;
    padding-bottom: 1.25rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: oklch(97.4% 0.008 145);
    border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label {
    color: var(--muted);
}

.stButton > button {
    min-height: 2.35rem;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    background: var(--panel) !important;
    box-shadow: none !important;
    transition:
        background 180ms cubic-bezier(.22,1,.36,1),
        border-color 180ms cubic-bezier(.22,1,.36,1),
        transform 180ms cubic-bezier(.22,1,.36,1);
}

.stButton > button p {
    color: inherit !important;
    white-space: nowrap;
}

.stButton > button:hover {
    background: var(--accent-soft) !important;
    border-color: color-mix(in oklch, var(--accent) 45%, var(--line)) !important;
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0);
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    justify-content: flex-start;
    border: 1px solid transparent;
    border-radius: 8px;
    color: var(--text);
    background: transparent;
    transition: background 180ms cubic-bezier(.22,1,.36,1), border-color 180ms cubic-bezier(.22,1,.36,1);
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--panel);
    border-color: var(--line);
}

.nav-active {
    display: block;
    margin: .08rem 0 .34rem;
    padding: .62rem .7rem;
    border-radius: 8px;
    color: var(--text);
    background: var(--accent-soft);
    border: 1px solid color-mix(in oklch, var(--accent) 42%, var(--line));
    font-size: .9rem;
    font-weight: 650;
}

.app-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: .2rem 0 1.1rem;
    border-bottom: 1px solid var(--line);
}

.brand-lockup {
    display: flex;
    align-items: center;
    gap: .7rem;
}

.brand-mark {
    width: 1.85rem;
    height: 1.85rem;
    border-radius: 8px;
    display: grid;
    place-items: center;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: .75rem;
    font-weight: 750;
    letter-spacing: 0;
}

.eyebrow {
    margin: 0;
    font-size: .76rem;
    line-height: 1.2;
    color: var(--muted);
}

.screen-title {
    margin: 0;
    font-size: 1.06rem;
    line-height: 1.25;
    letter-spacing: 0;
}

.date-pill {
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: .36rem .72rem;
    color: var(--muted);
    background: var(--panel);
    font-size: .78rem;
}

.section-title {
    margin: 0;
    color: var(--text);
    font-size: .85rem;
    line-height: 1.2;
    font-weight: 700;
    letter-spacing: 0;
}

.muted {
    color: var(--muted);
}

.day-timeline {
    position: relative;
    display: grid;
    grid-template-columns: 3.4rem minmax(0, 1fr);
    min-height: 45.6rem;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: color-mix(in oklch, var(--panel) 76%, var(--surface));
    overflow: hidden;
    animation: slideFade 240ms cubic-bezier(.22,1,.36,1) both;
}

.cal-hours {
    display: grid;
    grid-template-rows: repeat(24, minmax(1.9rem, 1fr));
    border-right: 1px solid var(--line);
    background: color-mix(in oklch, var(--surface) 74%, var(--panel));
}

.cal-hour {
    padding: .18rem .42rem 0 0;
    border-bottom: 1px solid color-mix(in oklch, var(--line) 72%, transparent);
    color: var(--muted);
    font-size: .66rem;
    line-height: 1.1;
    text-align: right;
    font-variant-numeric: tabular-nums;
}

.cal-hour:last-child {
    border-bottom: 0;
}

.cal-grid {
    position: relative;
    display: grid;
    grid-template-rows: repeat(24, minmax(1.9rem, 1fr));
    background:
        repeating-linear-gradient(
            to bottom,
            transparent 0,
            transparent calc((100% / 24) - 1px),
            color-mix(in oklch, var(--line) 68%, transparent) calc((100% / 24) - 1px),
            color-mix(in oklch, var(--line) 68%, transparent) calc(100% / 24)
        );
}

.cal-event {
    position: absolute;
    left: .55rem;
    right: .55rem;
    min-height: 2.15rem;
    padding: .42rem .52rem;
    border: 1px solid color-mix(in oklch, var(--accent) 28%, var(--line));
    border-radius: 7px;
    background: color-mix(in oklch, var(--accent-soft) 68%, var(--panel));
    overflow: hidden;
    box-shadow: 0 1px 0 color-mix(in oklch, var(--accent) 18%, transparent);
}

.cal-event-time {
    color: var(--muted);
    font-size: .66rem;
    line-height: 1.2;
    margin-bottom: .14rem;
    font-variant-numeric: tabular-nums;
}

.cal-event-title {
    color: var(--text);
    font-weight: 650;
    font-size: .78rem;
    line-height: 1.22;
    overflow-wrap: anywhere;
}

.cal-now {
    position: absolute;
    left: 0;
    right: 0;
    height: 1px;
    background: var(--accent);
    box-shadow: 0 0 0 1px color-mix(in oklch, var(--accent) 16%, transparent);
}

.cal-now::before {
    content: "";
    position: absolute;
    left: -.25rem;
    top: -.2rem;
    width: .42rem;
    height: .42rem;
    border-radius: 999px;
    background: var(--accent);
}

.cal-open-day {
    position: absolute;
    left: .72rem;
    right: .72rem;
    top: 50%;
    transform: translateY(-50%);
    padding: .6rem .7rem;
    border: 1px dashed color-mix(in oklch, var(--soft) 72%, var(--line));
    border-radius: 8px;
    background: color-mix(in oklch, var(--panel) 82%, transparent);
    color: var(--muted);
    font-size: .78rem;
    line-height: 1.35;
    text-align: center;
}

.cal-all-day {
    margin-bottom: .55rem;
    display: grid;
    gap: .4rem;
}

.cal-all-day .cal-event {
    position: static;
}

.plan-list {
    display: grid;
    gap: .48rem;
}

.todo-panel {
    padding: .9rem;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: color-mix(in oklch, var(--panel) 88%, var(--surface));
}

.todo-panel [data-testid="stCheckbox"] {
    padding: .08rem 0;
}

.todo-panel [data-testid="stCheckbox"] label {
    align-items: flex-start;
    gap: .5rem;
}

.todo-panel [data-testid="stCheckbox"] p {
    color: var(--text);
    font-size: .86rem;
    line-height: 1.35;
}

.todo-panel [data-testid="stCheckbox"] input:checked + div {
    border-color: var(--accent);
    background: var(--accent);
}

[data-testid="stCheckbox"] p {
    color: var(--text) !important;
    font-size: .88rem;
    line-height: 1.35;
}

.plan-row {
    display: grid;
    grid-template-columns: .9rem 1fr;
    gap: .55rem;
    align-items: start;
    color: var(--muted);
    font-size: .82rem;
    line-height: 1.4;
}

.dot {
    width: .48rem;
    height: .48rem;
    margin-top: .33rem;
    border-radius: 999px;
    border: 1px solid var(--accent);
    background: var(--panel);
}

.empty-note {
    padding: .8rem .9rem;
    border-radius: 8px;
    background: var(--panel);
    border: 1px solid var(--line);
    color: var(--muted);
    font-size: .82rem;
    line-height: 1.45;
}

.trace {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: .4rem;
    margin: -.45rem 0 .95rem 3.1rem;
}

.trace-chip {
    display: inline-flex;
    align-items: center;
    min-height: 1.55rem;
    padding: .18rem .52rem;
    border-radius: 999px;
    border: 1px solid var(--line);
    background: var(--panel);
    color: var(--muted);
    font-size: .72rem;
    animation: chipIn 200ms cubic-bezier(.22,1,.36,1) both;
}

.metric-strip {
    margin-top: .8rem;
    border-top: 0;
    padding-top: 0;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: .85rem;
}

.metric {
    min-height: 3.55rem;
    padding: .68rem .78rem;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: color-mix(in oklch, var(--panel) 82%, transparent);
}

.metric-label {
    color: var(--muted);
    font-size: .72rem;
    line-height: 1.2;
    margin-bottom: .35rem;
}

.metric-value {
    color: var(--text);
    font-size: 1rem;
    line-height: 1.2;
    font-weight: 720;
}

.metric-bar {
    height: .18rem;
    background: var(--panel-strong);
    border-radius: 999px;
    margin-top: .72rem;
    overflow: hidden;
}

.metric-fill {
    height: 100%;
    border-radius: 999px;
    background: var(--accent);
}

.quick-actions {
    margin: .9rem 0 .9rem;
}

.chat-thread {
    height: clamp(12rem, calc(100vh - 33rem), 21rem);
    overflow-y: auto;
    overscroll-behavior: contain;
    padding: 1rem .2rem 1.15rem 0;
    border-bottom: 1px solid var(--line);
    scrollbar-width: thin;
    scrollbar-color: color-mix(in oklch, var(--accent) 30%, var(--line)) transparent;
    scroll-behavior: smooth;
}

.chat-thread::-webkit-scrollbar {
    width: .5rem;
}

.chat-thread::-webkit-scrollbar-track {
    background: transparent;
}

.chat-thread::-webkit-scrollbar-thumb {
    background: color-mix(in oklch, var(--accent) 28%, var(--line));
    border-radius: 999px;
}

.message-row {
    display: flex;
    gap: .78rem;
    align-items: flex-start;
    max-width: 74ch;
    margin: 0 0 .92rem;
    animation: slideFade 240ms cubic-bezier(.22,1,.36,1) both;
}

.message-row.user {
    margin-left: auto;
    flex-direction: row-reverse;
}

.message-avatar {
    width: 1.82rem;
    height: 1.82rem;
    flex: 0 0 auto;
    display: grid;
    place-items: center;
    border-radius: 8px;
    background: var(--accent-soft);
    color: var(--accent);
    font-size: .74rem;
    font-weight: 760;
}

.message-row.user .message-avatar {
    background: var(--panel-strong);
    color: var(--muted);
}

.message-copy {
    padding-top: .08rem;
    color: var(--text);
    font-size: .94rem;
    line-height: 1.58;
}

.message-copy p {
    margin: 0 0 .72rem;
}

.message-copy p:last-child {
    margin-bottom: 0;
}

.message-copy strong {
    color: var(--text);
    font-weight: 760;
}

.message-copy ul,
.message-copy ol {
    margin: .45rem 0 .75rem 1.1rem;
    padding: 0;
}

.message-copy li {
    margin: .18rem 0;
    padding-left: .18rem;
}

.message-copy code {
    padding: .08rem .28rem;
    border-radius: 5px;
    background: var(--panel-strong);
    color: var(--text);
    font-size: .88em;
}

.message-copy table {
    display: block;
    max-width: 100%;
    margin: .75rem 0 1rem;
    overflow-x: auto;
    border-collapse: collapse;
    border-spacing: 0;
    color: var(--text);
    font-size: .82rem;
    line-height: 1.38;
    scrollbar-width: thin;
    scrollbar-color: color-mix(in oklch, var(--accent) 30%, var(--line)) transparent;
}

.message-copy th,
.message-copy td {
    min-width: 8.5rem;
    padding: .52rem .62rem;
    border: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
}

.message-copy th {
    background: var(--panel-strong);
    color: var(--text);
    font-weight: 720;
}

.message-copy td {
    background: color-mix(in oklch, var(--panel) 72%, transparent);
}

.message-row.user .message-copy {
    max-width: 58ch;
    padding: .62rem .78rem;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--panel);
}

.context-stack {
    display: grid;
    gap: 1.05rem;
    position: sticky;
    top: 4.7rem;
    max-height: calc(100vh - 5.4rem);
    overflow-y: auto;
    overscroll-behavior: contain;
    padding: 0 .25rem .15rem 0;
    scrollbar-width: thin;
    scrollbar-color: color-mix(in oklch, var(--accent) 30%, var(--line)) transparent;
}

.context-stack .day-timeline {
    min-height: 0;
    height: clamp(28rem, calc(100vh - 24rem), 42rem);
}

.context-stack .cal-hours,
.context-stack .cal-grid {
    grid-template-rows: repeat(24, minmax(0, 1fr));
}

.context-stack .cal-event {
    min-height: 1.45rem;
    padding: .24rem .42rem;
}

.context-stack .cal-event-time {
    font-size: .6rem;
    margin-bottom: .08rem;
}

.context-stack .cal-event-title {
    font-size: .7rem;
    line-height: 1.1;
}

.context-stack::-webkit-scrollbar {
    width: .46rem;
}

.context-stack::-webkit-scrollbar-track {
    background: transparent;
}

.context-stack::-webkit-scrollbar-thumb {
    background: color-mix(in oklch, var(--accent) 28%, var(--line));
    border-radius: 999px;
}

.st-key-main_workspace {
    min-height: 0;
}

.st-key-main_workspace > [data-testid="stVerticalBlock"],
.st-key-main_workspace > div > [data-testid="stVerticalBlock"] {
    min-height: 0;
}

.st-key-metrics_dock {
    margin-top: .8rem;
    padding-top: 0;
}

.st-key-side_workspace {
    height: calc(100vh - 5.4rem);
    min-height: 0;
    overflow: hidden;
}

.st-key-calendar_panel,
.st-key-todo_panel {
    min-height: 0;
    overflow: hidden;
}

.st-key-calendar_panel {
    height: min(56vh, 31rem);
}

.st-key-todo_panel {
    height: min(24vh, 14rem);
    margin-top: .85rem;
}

.st-key-calendar_panel [data-testid="stVerticalBlock"] {
    height: 100%;
}

.st-key-calendar_panel .rail-section {
    padding-top: 0;
}

.st-key-calendar_panel .day-timeline {
    min-height: 0;
    height: calc(100% - 2.05rem);
}

.st-key-calendar_panel .cal-hours,
.st-key-calendar_panel .cal-grid {
    grid-template-rows: repeat(24, minmax(.8rem, 1fr));
}

.st-key-calendar_panel .cal-event {
    min-height: 1.45rem;
    padding: .24rem .42rem;
}

.st-key-calendar_panel .cal-event-time {
    font-size: .6rem;
    margin-bottom: .08rem;
}

.st-key-calendar_panel .cal-event-title {
    font-size: .7rem;
    line-height: 1.1;
}

.st-key-todo_panel > [data-testid="stVerticalBlock"] {
    height: 100%;
    gap: 0;
}

.st-key-todo_panel [data-testid="stVerticalBlockBorderWrapper"] {
    height: 100%;
    overflow-y: auto;
    overscroll-behavior: contain;
    scrollbar-width: thin;
    scrollbar-color: color-mix(in oklch, var(--accent) 30%, var(--line)) transparent;
}

.st-key-todo_panel [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"] {
    gap: 0;
    padding: 0;
    min-height: 100%;
}

.st-key-todo_panel [data-testid="stHtml"] {
    margin: 0;
    padding: 0;
}

.plan-card-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: .75rem;
    padding: .68rem .9rem;
    border-bottom: 1px solid var(--line);
    line-height: 1.2;
}

.st-key-todo_panel [data-testid="stCheckbox"] {
    padding: .48rem .9rem;
    border-bottom: 1px solid color-mix(in oklch, var(--line) 55%, transparent);
    margin: 0;
}

.st-key-todo_panel [data-testid="stCheckbox"]:last-of-type {
    border-bottom: none;
}

.st-key-todo_panel [data-testid="stCheckbox"] label {
    align-items: center;
    gap: .55rem;
    background: transparent !important;
}

.st-key-todo_panel [data-testid="stCheckbox"] p {
    color: var(--text);
    font-size: .84rem;
    line-height: 1.3;
    margin: 0;
    transition: color 180ms cubic-bezier(.22,1,.36,1);
}

.st-key-todo_panel [data-testid="stCheckbox"] label:has(input:checked) > span {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}

.st-key-todo_panel [data-testid="stCheckbox"] label > div {
    background: transparent !important;
}

.st-key-todo_panel [data-testid="stCheckbox"]:has(input:checked) p {
    color: var(--muted) !important;
    text-decoration: line-through;
    text-decoration-color: color-mix(in oklch, var(--muted) 55%, transparent);
}

.st-key-todo_panel [data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar {
    width: .46rem;
}

.st-key-todo_panel [data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar-track {
    background: transparent;
}

.st-key-todo_panel [data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar-thumb {
    background: color-mix(in oklch, var(--accent) 28%, var(--line));
    border-radius: 999px;
}

.rail-section {
    padding: .95rem 0 1.05rem;
    border-bottom: 1px solid var(--line);
}

.rail-section:last-child {
    border-bottom: 0;
}

.rail-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: .75rem;
    margin-bottom: .72rem;
}

.rail-meta {
    color: var(--muted);
    font-size: .72rem;
}

[data-testid="stForm"] {
    margin-top: .9rem;
    padding: .64rem;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: color-mix(in oklch, var(--panel) 88%, var(--surface));
    position: static;
    box-shadow: none;
}

[data-testid="stForm"] [data-testid="stTextInput"] input {
    min-height: 2.8rem;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    background: var(--panel) !important;
    color: var(--text) !important;
    box-shadow: none !important;
}

[data-testid="stForm"] [data-testid="stTextInput"] input:focus {
    border-color: color-mix(in oklch, var(--accent) 55%, var(--line)) !important;
    box-shadow: 0 0 0 3px color-mix(in oklch, var(--accent-soft) 55%, transparent) !important;
}

[data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
    min-height: 2.8rem;
    font-weight: 680;
    color: var(--panel) !important;
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    white-space: nowrap;
}

[data-testid="stForm"] [data-testid="stFormSubmitButton"] button p {
    color: inherit !important;
    white-space: nowrap;
}

.view-panel {
    padding: .85rem 0 0;
}

.view-panel h2 {
    margin: 0 0 .65rem;
    color: var(--text);
    font-size: 1.1rem;
    line-height: 1.25;
    letter-spacing: 0;
}

.view-copy {
    max-width: 68ch;
    color: var(--muted);
    font-size: .9rem;
    line-height: 1.55;
}

@keyframes slideFade {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes chipIn {
    from { opacity: 0; transform: translateY(3px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: .01ms !important;
        transition-duration: .01ms !important;
        scroll-behavior: auto !important;
    }
}

@media (max-width: 900px) {
    .block-container {
        padding-top: 2.4rem;
    }

    .app-title {
        align-items: flex-start;
        flex-direction: column;
    }

    .metric-strip {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .trace {
        margin-left: 0;
    }

    .chat-thread {
        height: clamp(14rem, calc(100vh - 25rem), 24rem);
    }

    .context-stack,
    [data-testid="stForm"] {
        position: static;
        max-height: none;
        overflow: visible;
        box-shadow: none;
    }
}
</style>
"""


TOOL_LABELS = {
    "list_calendar_events": "Calendar",
    "create_calendar_event": "Calendar write",
    "update_calendar_event": "Calendar write",
    "delete_calendar_event": "Calendar write",
    "retrieve_user_facts": "Memory",
    "store_user_fact": "Memory",
    "retrieve_past_logs": "Past logs",
    "save_conversation_log": "Conversation log",
    "get_daily_plan": "Daily plan",
    "save_daily_plan": "Daily plan",
    "get_daily_tasks": "Daily tasks",
    "save_daily_tasks": "Daily tasks",
    "set_daily_task_completion": "Daily tasks",
    "set_daily_subtask_completion": "Daily tasks",
    "log_habit": "Habits",
    "get_habit_streaks": "Habits",
    "update_habit_streaks": "Habits",
}

LOCAL_TOOLS = [
    retrieve_user_facts,
    store_user_fact,
    retrieve_past_logs,
    save_conversation_log,
    get_daily_plan,
    save_daily_plan,
    get_daily_tasks,
    save_daily_tasks,
    set_daily_task_completion,
    set_daily_subtask_completion,
    log_habit,
    get_habit_streaks,
    update_habit_streaks,
]

NAV_ITEMS = ["Coach", "Plan", "Calendar", "Habits", "Notes", "Sources", "Settings"]
MARKDOWN = MarkdownIt("commonmark", {"html": False, "linkify": False}).enable("table")


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: dict[str, Any] = {}

    def runner() -> None:
        result["value"] = asyncio.run(coro)

    thread = threading.Thread(target=runner)
    thread.start()
    thread.join()
    return result["value"]


@st.cache_resource(show_spinner=False)
def get_agent_executor():
    calendar_tools = _run_async(build_calendar_mcp_client().get_tools())
    return build_agent(
        [*calendar_tools, *LOCAL_TOOLS],
        return_intermediate_steps=True,
    )


def _parse_json_or_none(value: str) -> Any | None:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def _format_event_time(value: str) -> str:
    if not value:
        return ""
    if "T" not in value:
        return "All day"

    cleaned = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return value
    return parsed.strftime("%H:%M")


def _event_minute(day: str, value: str, fallback: int) -> int:
    if not value or "T" not in value:
        return fallback

    cleaned = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        return fallback

    current_day = date.fromisoformat(day)
    if parsed.date() < current_day:
        return 0
    if parsed.date() > current_day:
        return 24 * 60
    return parsed.hour * 60 + parsed.minute


def _calendar_hour_labels() -> str:
    labels = []
    for hour in range(24):
        label = "00:00" if hour == 0 else f"{hour:02d}:00"
        labels.append(f'<div class="cal-hour">{label}</div>')
    return "".join(labels)


def _now_marker(day: str) -> str:
    today = date.today().isoformat()
    if day != today:
        return ""

    now = datetime.now()
    top = ((now.hour * 60 + now.minute) / (24 * 60)) * 100
    return f'<div class="cal-now" style="top:{top:.3f}%"></div>'


def _calendar_event_block(event: dict[str, Any], day: str) -> str:
    start_raw = event.get("start", "")
    end_raw = event.get("end", "")
    start = _format_event_time(start_raw)
    end = _format_event_time(end_raw)
    title = html.escape(event.get("title", "Untitled"))

    if start == "All day":
        return f"""
<div class="cal-event">
    <div class="cal-event-time">All day</div>
    <div class="cal-event-title">{title}</div>
</div>
"""

    start_minute = max(0, min(24 * 60, _event_minute(day, start_raw, 0)))
    end_minute = max(0, min(24 * 60, _event_minute(day, end_raw, start_minute + 30)))
    if end_minute <= start_minute:
        end_minute = min(24 * 60, start_minute + 30)

    top = (start_minute / (24 * 60)) * 100
    height = ((end_minute - start_minute) / (24 * 60)) * 100
    time_range = f"{html.escape(start)} - {html.escape(end)}"
    return f"""
<div class="cal-event" style="top:calc({top:.3f}% + .14rem);height:max(2.15rem, calc({height:.3f}% - .28rem));">
    <div class="cal-event-time">{time_range}</div>
    <div class="cal-event-title">{title}</div>
</div>
"""


def _day_timeline_html(day: str, events: list[dict[str, Any]]) -> str:
    all_day_events = [
        event for event in events if _format_event_time(event.get("start", "")) == "All day"
    ]
    timed_events = [
        event for event in events if _format_event_time(event.get("start", "")) != "All day"
    ]
    all_day = ""
    if all_day_events:
        all_day_blocks = "".join(
            _calendar_event_block(event, day) for event in all_day_events
        )
        all_day = f'<div class="cal-all-day">{all_day_blocks}</div>'

    open_day = ""
    if not events:
        open_day = '<div class="cal-open-day">No scheduled events today</div>'

    return (
        all_day
        + '<div class="day-timeline">'
        + f'<div class="cal-hours">{_calendar_hour_labels()}</div>'
        + '<div class="cal-grid">'
        + open_day
        + "".join(_calendar_event_block(event, day) for event in timed_events)
        + _now_marker(day)
        + "</div>"
        + "</div>"
    )


@st.cache_data(ttl=90, show_spinner=False)
def get_calendar_preview(day: str) -> dict[str, Any]:
    try:
        raw = _list_calendar_events(day)
    except Exception as exc:
        return {"status": "error", "message": str(exc), "events": []}

    parsed = _parse_json_or_none(raw)
    if isinstance(parsed, list):
        return {"status": "ok", "message": "", "events": parsed}
    return {"status": "empty", "message": raw, "events": []}


@st.cache_data(ttl=30, show_spinner=False)
def get_plan_preview(day: str) -> str:
    return get_daily_plan.invoke({"date": day})


@st.cache_data(ttl=30, show_spinner=False)
def get_task_preview(day: str) -> list[dict[str, Any]]:
    raw = get_daily_tasks.invoke({"date": day})
    parsed = _parse_json_or_none(raw)
    if not isinstance(parsed, dict):
        return []
    tasks = parsed.get("tasks", [])
    return tasks if isinstance(tasks, list) else []


@st.cache_data(ttl=30, show_spinner=False)
def get_habit_preview() -> dict[str, Any]:
    raw = get_habit_streaks.invoke({})
    parsed = _parse_json_or_none(raw)
    return parsed if isinstance(parsed, dict) else {}


def _message_history() -> list[HumanMessage | AIMessage]:
    history = []
    for message in st.session_state.messages[:-1]:
        if message["role"] == "user":
            history.append(HumanMessage(content=message["content"]))
        elif message["role"] == "assistant":
            history.append(AIMessage(content=message["content"]))
    return history


def _extract_sources(result: dict[str, Any]) -> list[str]:
    labels = []
    for step in result.get("intermediate_steps", []) or []:
        action = step[0] if isinstance(step, tuple) else None
        name = getattr(action, "tool", None)
        label = TOOL_LABELS.get(name, name)
        if label and label not in labels:
            labels.append(label)
    return labels


def remember_later(message: str) -> None:
    thread = threading.Thread(
        target=extract_and_store_facts,
        args=(message,),
        daemon=True,
    )
    thread.start()


def render_trace(sources: list[str]) -> None:
    if not sources:
        return
    chips = "".join(
        f'<span class="trace-chip">Used {html.escape(source)}</span>'
        for source in sources
    )
    st.html(f'<div class="trace">{chips}</div>')


def render_message_content(content: str) -> str:
    return MARKDOWN.render(content)


def calendar_html(day: str) -> str:
    preview = get_calendar_preview(day)
    item_count = len(preview["events"])
    meta = "empty" if item_count == 0 else f"{item_count} item{'s' if item_count != 1 else ''}"
    head = (
        '<div class="rail-head">'
        '<p class="section-title">Calendar</p>'
        f'<span class="rail-meta">{meta}</span>'
        "</div>"
    )

    if preview["status"] == "error":
        return (
            head
            + '<div class="empty-note">Calendar unavailable: '
            + html.escape(preview["message"])
            + "</div>"
        )

    return head + _day_timeline_html(day, preview["events"])


def render_calendar(day: str) -> None:
    st.html(calendar_html(day))


def _plan_lines(plan_text: str) -> list[str]:
    if not plan_text or plan_text == "No plan found":
        return []
    lines = [line.strip(" -\t") for line in plan_text.splitlines()]
    return [line for line in lines if line][:7]


def _flat_todos(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    todos = []
    for task in tasks:
        if task.get("id"):
            todos.append(
                {
                    "id": task["id"],
                    "kind": "task",
                    "title": str(task.get("title", "Untitled")),
                    "completed": bool(task.get("completed")),
                }
            )
        subtasks = task.get("subtasks", [])
        if isinstance(subtasks, list):
            for subtask in subtasks:
                if subtask.get("id"):
                    todos.append(
                        {
                            "id": subtask["id"],
                            "kind": "subtask",
                            "title": str(subtask.get("title", "Untitled")),
                            "completed": bool(subtask.get("completed")),
                        }
                    )
    return todos


def _task_counts(tasks: list[dict[str, Any]]) -> tuple[int, int]:
    todos = _flat_todos(tasks)
    return sum(1 for todo in todos if todo["completed"]), len(todos)


def plan_html(day: str) -> str:
    tasks = get_task_preview(day)
    completed, total = _task_counts(tasks)
    meta = "not set" if not tasks else f"{completed}/{total} done"
    head = (
        '<div class="rail-head">'
        '<p class="section-title">Daily plan</p>'
        f'<span class="rail-meta">{meta}</span>'
        "</div>"
    )
    if not tasks:
        return (
            head
            + '<div class="empty-note">No todo plan saved yet. Agree on a plan with Bud, '
            + "then it will appear here as tasks.</div>"
        )

    rows = "".join(
        '<div class="plan-row"><span class="dot"></span>'
        f'<span>{html.escape(todo["title"])}</span></div>'
        for todo in _flat_todos(tasks)[:8]
    )
    return f'{head}<div class="plan-list">{rows}</div>'


def _sync_task_completion(task_id: Any, completed: bool) -> None:
    set_daily_task_completion.invoke({"task_id": int(task_id), "completed": completed})
    st.cache_data.clear()
    st.rerun()


def _sync_subtask_completion(subtask_id: Any, completed: bool) -> None:
    set_daily_subtask_completion.invoke(
        {"subtask_id": int(subtask_id), "completed": completed}
    )
    st.cache_data.clear()
    st.rerun()


def _toggle_todo(todo: dict[str, Any], completed: bool) -> None:
    if todo["kind"] == "subtask":
        _sync_subtask_completion(todo["id"], completed)
    else:
        _sync_task_completion(todo["id"], completed)


def render_todo_plan(day: str, *, compact: bool = False) -> None:
    tasks = get_task_preview(day)
    todos = _flat_todos(tasks)
    completed = sum(1 for todo in todos if todo["completed"])
    meta = "not set" if not todos else f"{completed}/{len(todos)} done"

    todo_container = st.container(border=True)
    with todo_container:
        st.html(
            f'<div class="plan-card-head">'
            f'<p class="section-title">Daily plan</p>'
            f'<span class="rail-meta">{meta}</span>'
            f"</div>"
        )
        if not todos:
            st.html(
                '<div class="empty-note" style="margin:.6rem .9rem .7rem;">'
                "No todo plan saved yet. Agree on a plan with Bud, "
                "then it will appear here as tasks.</div>"
            )
            return
        for todo in todos:
            key = f"{'compact_' if compact else 'plan_'}todo_{todo['kind']}_{todo['id']}"
            checked = st.checkbox(todo["title"], value=todo["completed"], key=key)
            if checked != todo["completed"]:
                _toggle_todo(todo, checked)


def render_plan(day: str) -> None:
    render_todo_plan(day, compact=False)


def _habit_metrics(day: str) -> list[dict[str, str | int]]:
    habits = get_habit_preview()
    plan_exists = bool(get_task_preview(day) or _plan_lines(get_plan_preview(day)))

    if habits:
        completion_rates = [
            float(details.get("completion_rate", 0))
            for details in habits.values()
            if isinstance(details, dict)
        ]
        current_streaks = [
            int(details.get("current_streak", 0))
            for details in habits.values()
            if isinstance(details, dict)
        ]
        average_rate = (
            round(sum(completion_rates) / len(completion_rates) * 100)
            if completion_rates
            else 0
        )
        best_streak = max(current_streaks) if current_streaks else 0
        tracked = len(habits)
    else:
        average_rate = 0
        best_streak = 0
        tracked = 0

    return [
        {
            "label": "Plan state",
            "value": "Set" if plan_exists else "Open",
            "fill": 100 if plan_exists else 20,
        },
        {"label": "Tracked habits", "value": str(tracked), "fill": min(tracked * 25, 100)},
        {"label": "Habit score", "value": f"{average_rate}%", "fill": average_rate},
        {"label": "Best streak", "value": f"{best_streak} days", "fill": min(best_streak * 8, 100)},
    ]


def render_metric_strip(day: str) -> None:
    metrics = _habit_metrics(day)
    cards = "".join(
        (
            '<div class="metric">'
            f'<div class="metric-label">{html.escape(str(metric["label"]))}</div>'
            f'<div class="metric-value">{html.escape(str(metric["value"]))}</div>'
            '<div class="metric-bar">'
            f'<div class="metric-fill" style="width:{int(metric["fill"])}%"></div>'
            "</div>"
            "</div>"
        )
        for metric in metrics
    )
    st.html(f'<div class="metric-strip">{cards}</div>')


def render_context_stack(day: str, calendar_first: bool = True) -> None:
    sections = [calendar_html(day), plan_html(day)]
    if not calendar_first:
        sections.reverse()
    section_html = "".join(
        f'<section class="rail-section">{section}</section>' for section in sections
    )
    st.html(f'<div class="context-stack">{section_html}</div>')


def send_to_agent(prompt: str) -> tuple[str, list[str]]:
    agent = get_agent_executor()
    result = _run_async(
        agent.ainvoke(
            {
                "input": prompt,
                "chat_history": _message_history(),
                "system_prompt": build_system_prompt(),
            }
        )
    )
    return result.get("output", ""), _extract_sources(result)


def queue_prompt(prompt: str) -> None:
    st.session_state.pending_prompt = prompt
    st.rerun()


def set_active_view(view: str) -> None:
    st.session_state.active_view = view


def render_header(title: str, eyebrow: str = "Today") -> None:
    st.html(
        f"""
<div class="app-title">
    <div>
        <p class="eyebrow">{html.escape(eyebrow)}</p>
        <h1 class="screen-title">{html.escape(title)}</h1>
    </div>
    <div class="date-pill">{datetime.now().strftime("%A, %B %-d")}</div>
</div>
"""
    )


def render_quick_actions() -> None:
    st.html('<div class="quick-actions"></div>')
    quick_cols = st.columns(3, gap="small")
    prompts = [
        ("Plan my day", "Plan my day using my calendar, habits, and saved context."),
        ("Check in", "Help me check in and adjust the rest of today."),
        ("Reflect", "Guide me through an evening reflection for today."),
    ]
    for column, (label, prompt) in zip(quick_cols, prompts, strict=True):
        with column:
            if st.button(label, use_container_width=True):
                queue_prompt(prompt)


def render_chat() -> None:
    rows = ""
    for message in st.session_state.messages:
        role = message["role"]
        label = "You" if role == "user" else "Bud"
        text = render_message_content(message["content"])
        source_chips = ""
        if role == "assistant" and message.get("sources"):
            source_chips = "".join(
                f'<span class="trace-chip">Used {html.escape(source)}</span>'
                for source in message["sources"]
            )
            source_chips = f'<div class="trace">{source_chips}</div>'
        rows += (
            f'<div class="message-row {role}">'
            f'<div class="message-avatar">{label[:2]}</div>'
            f'<div><div class="message-copy">{text}</div>{source_chips}</div>'
            "</div>"
        )
    st.html(f'<div class="chat-thread">{rows}</div>')


def render_input_panel() -> str | None:
    with st.form("coach_message_form", clear_on_submit=True):
        input_col, send_col = st.columns([0.82, 0.18], gap="small")
        with input_col:
            typed = st.text_input(
                "Message Bud",
                label_visibility="collapsed",
                placeholder="Message Bud...",
            )
        with send_col:
            submitted = st.form_submit_button("Send", use_container_width=True)
    if submitted and typed.strip():
        queue_prompt(typed.strip())
    return None


def render_notes_view() -> None:
    st.html(
        """
<div class="view-panel">
    <h2>Memory notes</h2>
    <p class="view-copy">
        These are the kinds of personal facts Bud can retrieve while coaching:
        goals, recurring schedule constraints, preferences, and habit patterns.
    </p>
</div>
"""
    )
    raw = retrieve_user_facts.invoke(
        {"query": "goals habits schedule constraints preferences", "k": 6}
    )
    facts = _parse_json_or_none(raw)
    if not isinstance(facts, list) or not facts:
        st.html('<div class="empty-note">No stored facts found yet.</div>')
        return

    rows = "".join(
        (
            '<div class="plan-row"><span class="dot"></span>'
            f'<span>{html.escape(str(fact))}</span></div>'
        )
        for fact in facts
    )
    st.html(f'<div class="plan-list">{rows}</div>')


def render_sources_view() -> None:
    st.html(
        """
<div class="view-panel">
    <h2>Grounding trace</h2>
    <p class="view-copy">
        After Bud responds, this area shows which systems were used. It is a
        trust signal for the app, not a raw developer log.
    </p>
</div>
"""
    )
    recent_sources = []
    for message in reversed(st.session_state.messages):
        if message["role"] == "assistant" and message.get("sources"):
            recent_sources = message["sources"]
            break

    if recent_sources:
        render_trace(recent_sources)
    else:
        st.html('<div class="empty-note">No tool trace yet. Ask Bud to plan the day.</div>')


def render_settings_view() -> None:
    st.html(
        """
<div class="view-panel">
    <h2>Settings</h2>
    <p class="view-copy">
        This first version keeps settings simple and visible for development.
        We can turn this into editable controls later.
    </p>
</div>
"""
    )
    st.code(
        "\n".join(
            [
                "OLLAMA_MODEL: from .env",
                "GOOGLE_CALENDAR_ID: primary by default",
                "DB_PATH: db/habits.db",
                "CHROMA_PATH: db/chroma",
            ]
        )
    )


st.markdown(CSS, unsafe_allow_html=True)

today = date.today().isoformat()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Good. We have the day in front of us. Tell me what kind of plan "
                "you need, and I will ground it in your calendar and current habits."
            ),
            "sources": [],
        }
    ]

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "active_view" not in st.session_state:
    st.session_state.active_view = "Coach"

prompt_to_process = st.session_state.pending_prompt
if prompt_to_process:
    st.session_state.pending_prompt = None
    st.session_state.messages.append(
        {"role": "user", "content": prompt_to_process, "sources": []}
    )
    with st.status("Grounding the answer", expanded=True) as status:
        st.write("Checking calendar, plan, habits, and memory.")
        try:
            output, sources = send_to_agent(prompt_to_process)
            status.update(label="Answer ready", state="complete", expanded=False)
        except Exception as exc:
            output = (
                "I could not complete that run. Check the model provider settings "
                f"and Calendar credentials.\n\n`{exc}`"
            )
            sources = []
            status.update(label="Run failed", state="error", expanded=False)

    st.session_state.messages.append(
        {"role": "assistant", "content": output, "sources": sources}
    )
    remember_later(prompt_to_process)
    st.cache_data.clear()
    st.rerun()

with st.sidebar:
    st.html(
        """
<div class="brand-lockup">
    <div class="brand-mark">AB</div>
    <div>
        <p class="screen-title">Accountability Bud</p>
        <p class="eyebrow">Private daily coach</p>
    </div>
</div>
"""
    )
    st.write("")
    for item in NAV_ITEMS:
        if st.session_state.active_view == item:
            st.html(f'<span class="nav-active">{item}</span>')
        elif st.button(item, key=f"nav_{item}", use_container_width=True):
            set_active_view(item)
            st.rerun()

main_col, side_col = st.columns([0.64, 0.36], gap="large")

with main_col:
    with st.container(key="main_workspace"):
        active_view = st.session_state.active_view
        render_header(active_view)

        if active_view == "Coach":
            render_quick_actions()
            render_chat()
            render_input_panel()
        elif active_view == "Plan":
            st.html(
                """
<div class="view-panel">
    <h2>Today&apos;s plan</h2>
    <p class="view-copy">
        This is the agreed plan for today. Bud saves it as todo tasks, and
        checking items here updates the same list shown in the side rail.
    </p>
</div>
"""
            )
            render_plan(today)
            if st.button("Ask Bud to update this plan", use_container_width=True):
                queue_prompt("Review and update today's saved plan using my current calendar.")
        elif active_view == "Calendar":
            st.html(
                """
<div class="view-panel">
    <h2>What&apos;s ahead</h2>
    <p class="view-copy">
        Calendar stays first because it is the ground truth for the day.
    </p>
</div>
"""
            )
            render_calendar(today)
        elif active_view == "Habits":
            st.html(
                """
<div class="view-panel">
    <h2>Accountability</h2>
    <p class="view-copy">
        Habit tracking stays quiet here: enough signal to keep you honest,
        without turning the product into a game.
    </p>
</div>
"""
            )
            if st.button("Run evening reflection", use_container_width=True):
                queue_prompt("Guide me through an evening reflection and update my habits.")
        elif active_view == "Notes":
            render_notes_view()
        elif active_view == "Sources":
            render_sources_view()
        elif active_view == "Settings":
            render_settings_view()

        with st.container(key="metrics_dock"):
            render_metric_strip(today)

with side_col:
    with st.container(key="side_workspace"):
        with st.container(key="calendar_panel"):
            render_calendar(today)
        with st.container(key="todo_panel"):
            render_todo_plan(today, compact=True)
