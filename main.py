#!/usr/bin/env python3
"""
AI Visibility Tracker — Main Entry Point

Searches 100 keywords across Google AI Overview, ChatGPT, and Claude
to check brand (Pristyn Care) visibility. All checks use Selenium browser automation.

Usage:
    python main.py
"""

from core.runner import run

if __name__ == "__main__":
    run()
