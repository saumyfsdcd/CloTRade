# Configuration file for API keys and settings
# Copy this file to config.py and add your actual API keys

import os

# OpenAI API Configuration
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY = "your-openai-api-key-here"

# Polygon API Configuration  
# Get your API key from: https://polygon.io/
POLYGON_API_KEY = "your-polygon-api-key-here"

# Trading Configuration
SYMBOL = "C:XAUUSD"  # Gold (XAUUSD)

# LLM Configuration
LLM_MODEL = "gpt-3.5-turbo"  # Using 3.5-turbo which is more widely available
TEMPERATURE = 0.1  # Low temperature for consistent trading decisions

# Optional: Environment Variables
# You can also set these as environment variables for better security:
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# POLYGON_API_KEY = os.getenv("POLYGON_API_KEY") 