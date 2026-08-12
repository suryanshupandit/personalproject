function switchTab(tabName) {
  // Hide all tabs
  const tabs = document.querySelectorAll('.tab-content');
  tabs.forEach(tab => tab.classList.remove('active'));
  
  // Deactivate all buttons
  const buttons = document.querySelectorAll('.tab-btn');
  buttons.forEach(btn => btn.classList.remove('active'));
  
  // Show selected tab and activate button
  document.getElementById(tabName).classList.add('active');
  event.target.classList.add('active');
}

function displayResult(resultDiv, data) {
  if (!data) {
    resultDiv.innerHTML = '<div class="result-box error">Error: No response received</div>';
    return;
  }
  
  const verdict = data.verdict || 'Unknown';
  const explanation = data.explanation || '';
  const analysis = data.analysis || {};
  
  // Determine verdict color
  let verdictClass = '';
  if (verdict.toLowerCase().includes('highly likely') || verdict.toLowerCase().includes('misinformation')) {
    verdictClass = 'high-ai';
  } else if (verdict.toLowerCase().includes('possibly') || verdict.toLowerCase().includes('uncertain')) {
    verdictClass = 'possibly-ai';
  } else {
    verdictClass = 'human';
  }
  
  let html = `
    <div class="result-box">
      <div class="verdict ${verdictClass}">📊 ${verdict}</div>
      <div class="explanation">${explanation}</div>
      <div class="analysis-grid">
  `;
  
  // Display analysis items
  for (const [key, value] of Object.entries(analysis)) {
    if (typeof value === 'object' && value !== null && value.value !== undefined) {
      const label = formatLabel(key);
      const itemValue = value.value || 'N/A';
      const meaning = value.meaning || '';
      
      html += `
        <div class="analysis-item">
          <div class="analysis-item-label">${label}</div>
          <div class="analysis-item-value">${itemValue}</div>
          <div class="analysis-item-meaning">${meaning}</div>
        </div>
      `;
    }
  }
  
  html += `</div></div>`;
  resultDiv.innerHTML = html;
}

function formatLabel(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
}

async function submitText() {
  const text = document.getElementById('textInput').value.trim();
  const resultDiv = document.getElementById('textResult');
  
  if (!text) {
    resultDiv.innerHTML = '<div class="result-box error">⚠️ Please enter some text to analyze</div>';
    return;
  }
  
  resultDiv.innerHTML = '<div class="loading">⏳ Analyzing text...</div>';
  
  try {
    const res = await fetch('/api/analyze/text', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    
    const data = await res.json();
    if (res.ok) {
      displayResult(resultDiv, data);
    } else {
      resultDiv.innerHTML = `<div class="result-box error">❌ Error: ${data.error || 'Unknown error'}</div>`;
    }
  } catch (error) {
    resultDiv.innerHTML = `<div class="result-box error">❌ Error: ${error.message}</div>`;
  }
}

async function submitImage() {
  const input = document.getElementById('imgFile');
  const resultDiv = document.getElementById('imgResult');
  
  if (!input.files || !input.files[0]) {
    resultDiv.innerHTML = '<div class="result-box error">⚠️ Please select an image file</div>';
    return;
  }
  
  resultDiv.innerHTML = '<div class="loading">⏳ Analyzing image...</div>';
  
  try {
    const fd = new FormData();
    fd.append('file', input.files[0]);
    
    const res = await fetch('/api/analyze/image', {
      method: 'POST',
      body: fd
    });
    
    const data = await res.json();
    if (res.ok) {
      displayResult(resultDiv, data);
    } else {
      resultDiv.innerHTML = `<div class="result-box error">❌ Error: ${data.error || 'Unknown error'}</div>`;
    }
  } catch (error) {
    resultDiv.innerHTML = `<div class="result-box error">❌ Error: ${error.message}</div>`;
  }
}

async function submitUrl() {
  const url = document.getElementById('urlInput').value.trim();
  const resultDiv = document.getElementById('urlResult');
  
  if (!url) {
    resultDiv.innerHTML = '<div class="result-box error">⚠️ Please enter a URL or article text</div>';
    return;
  }
  
  resultDiv.innerHTML = '<div class="loading">⏳ Analyzing article...</div>';
  
  try {
    // Check if it's a URL or just text
    const isUrl = url.startsWith('http://') || url.startsWith('https://');
    const endpoint = isUrl ? '/api/analyze/news' : '/api/analyze/text';
    const body = isUrl 
      ? JSON.stringify({ url })
      : JSON.stringify({ text: url });
    
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body
    });
    
    const data = await res.json();
    if (res.ok) {
      displayResult(resultDiv, data);
    } else {
      resultDiv.innerHTML = `<div class="result-box error">❌ Error: ${data.error || 'Unknown error'}</div>`;
    }
  } catch (error) {
    resultDiv.innerHTML = `<div class="result-box error">❌ Error: ${error.message}</div>`;
  }
}
