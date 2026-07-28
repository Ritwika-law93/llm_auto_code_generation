# Model used for all three pipeline stages (design, code, tests).
# Any OpenRouter-compatible model ID works here.
MODEL = "gpt-4o-mini"

# Lower temperature keeps output deterministic and structured.
# Raise toward 1.0 only if you want more creative / varied output.
TEMPERATURE = 0.3

# Hard cap on tokens returned per API call.
# 2000 is sufficient for focused stage output; increase for very large PRDs.
MAX_TOKENS = 2000
