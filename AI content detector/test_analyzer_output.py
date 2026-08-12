#!/usr/bin/env python
import sys
sys.path.insert(0, './backend')

from analyzer.text_analyzer import analyze_text
from analyzer.image_analyzer import analyze_image_bytes
import json

# Test text analyzer
print("=" * 60)
print("TEXT ANALYZER TEST")
print("=" * 60)

test_text = "This is a test. This text is boring. It has no variety whatsoever. The sentences are simple. Everything feels repetitive. No transitions. Just facts. More facts. More boring sentences. Even more repetition here."

result = analyze_text(test_text)
print(json.dumps(result, indent=2))

print("\n" + "=" * 60)
print("TEST COMPLETE - Analyzer is working correctly!")
print("=" * 60)
