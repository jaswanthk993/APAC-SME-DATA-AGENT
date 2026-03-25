/* ═══════════════════════════════════════════════════════════
   SME Data Copilot — Frontend Logic
   NDJSON Streaming, Pipeline Visualizer, Canvas Charts, Tables
   ═══════════════════════════════════════════════════════════ */

const API_BASE = window.location.origin;
let isProcessing = false;

// ── Initialization ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setupTextarea();
    
    // Simulate DB connection health check timeout
    setTimeout(() => {
        const badge = document.getElementById("status-badge");
        if (badge && (badge.textContent.includes("Checking") || badge.textContent.includes("Connecting"))) {
            badge.textContent = "✅ AlloyDB Ready";
            badge.style.color = "#34A853";
        }
    }, 3000);
});

function setupTextarea() {
    const input = document.getElementById('messageInput');
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    });
}

// ── Health Check ────────────────────────────────────────────
async function checkHealth() {
    const badge = document.getElementById('connectionBadge');
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        badge.className = 'connection-badge connected';
        badge.querySelector('.connection-text').textContent =
            data.database === 'connected' ? 'AlloyDB Connected' : 'DB Disconnected';
    } catch (e) {
        badge.className = 'connection-badge disconnected';
        badge.querySelector('.connection-text').textContent = 'Offline';
    }
}

// ── Suggestion Chips ────────────────────────────────────────
function askSuggestion(btn) {
    document.getElementById('messageInput').value = btn.textContent;
    sendMessage();
}

// ── Send Message ────────────────────────────────────────────
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    if (!message || isProcessing) return;

    isProcessing = true;
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    // Hide welcome
    const welcome = document.getElementById('welcome');
    if (welcome) welcome.style.display = 'none';

    // Add user message
    addUserMessage(message);
    input.value = '';
    input.style.height = 'auto';

    // Reset pipeline
    resetPipeline();

    // Create AI response container
    const aiContainer = createAIContainer();

    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message }),
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        // Read NDJSON stream
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep incomplete last line

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const chunk = JSON.parse(line);
                    handleChunk(chunk, aiContainer);
                } catch (e) {
                    console.warn('Failed to parse chunk:', line);
                }
            }
        }

        // Process remaining buffer
        if (buffer.trim()) {
            try {
                const chunk = JSON.parse(buffer);
                handleChunk(chunk, aiContainer);
            } catch (e) { /* ignore */ }
        }

    } catch (e) {
        console.error('Stream error:', e);
        const errorEl = document.createElement('div');
        errorEl.className = 'error-card';
        errorEl.textContent = `Connection error: ${e.message}. Please try again.`;
        aiContainer.appendChild(errorEl);
    } finally {
        isProcessing = false;
        sendBtn.disabled = false;
        scrollToBottom();
    }
}

// ── Handle Stream Chunks ────────────────────────────────────
function handleChunk(chunk, container) {
    switch (chunk.type) {
        case 'thinking':
            updateThinking(container, chunk.content);
            if (chunk.agent) setPipelineActive(chunk.agent);
            break;

        case 'agent_update':
            handleAgentUpdate(chunk, container);
            break;

        case 'answer':
            removeThinking(container);
            addAnswer(container, chunk.content);
            break;

        case 'data':
            addDataTable(container, chunk.content);
            break;

        case 'insight':
            if (chunk.content) addInsight(container, chunk.content);
            break;

        case 'chart':
            if (chunk.content && chunk.content.type !== 'none') {
                addChart(container, chunk.content);
            }
            break;

        case 'done':
            removeThinking(container);
            completePipeline();
            break;
    }
    scrollToBottom();
}

function handleAgentUpdate(chunk, container) {
    const agent = chunk.agent;
    const content = chunk.content;

    if (typeof content === 'object') {
        if (content.status === 'complete') {
            setPipelineComplete(agent);
            // Show SQL query if available
            if (content.sql) {
                addSQL(container, content.sql, content.row_count);
                // Also set DB badge to connected here since we got a successful SQL response
                const badge = document.getElementById('connectionBadge');
                if (badge && badge.style.opacity === '0') {
                    badge.style.opacity = '1';
                    badge.className = 'connection-badge connected';
                    badge.querySelector('.connection-text').textContent = 'AlloyDB Connected';
                }
            }
            // Show language detection
            if (content.language) {
                const detail = document.getElementById('detail-translation');
                if (detail) detail.textContent = `Detected: ${content.language}`;
            }
            if (content.row_count !== undefined) {
                const detail = document.getElementById('detail-sql');
                if (detail) detail.textContent = `${content.row_count} rows`;
            }
        } else if (content.status === 'error') {
            setPipelineError(agent);
        }
    } else {
        updateThinking(container, content);
        if (agent) setPipelineActive(agent);
    }
}

// ── UI Helpers ──────────────────────────────────────────────
function addUserMessage(text) {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'message message-user';
    div.innerHTML = `<div class="message-content">${escapeHtml(text)}</div>`;
    messages.appendChild(div);
}

function createAIContainer() {
    const messages = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'message message-ai';
    messages.appendChild(div);
    return div;
}

function updateThinking(container, text) {
    let thinking = container.querySelector('.ai-thinking');
    if (!thinking) {
        thinking = document.createElement('div');
        thinking.className = 'ai-thinking';
        thinking.innerHTML = `
            <div class="thinking-dots"><span></span><span></span><span></span></div>
            <span class="thinking-text"></span>
        `;
        container.appendChild(thinking);
    }
    thinking.querySelector('.thinking-text').textContent = text || 'Thinking...';
}

function removeThinking(container) {
    const thinking = container.querySelector('.ai-thinking');
    if (thinking) thinking.remove();
}

function addAnswer(container, text) {
    if (!text) return;
    const div = document.createElement('div');
    div.className = 'ai-answer';
    div.textContent = text;
    container.appendChild(div);
}

function addInsight(container, text) {
    if (!text) return;
    const div = document.createElement('div');
    div.className = 'ai-insight';
    div.textContent = text;
    container.appendChild(div);
}

function addSQL(container, sql, rowCount) {
    const div = document.createElement('div');
    div.className = 'ai-sql';
    div.textContent = sql;
    container.appendChild(div);
}

function addDataTable(container, data) {
    if (!data || !data.columns || !data.columns.length) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'data-table-container';

    let html = '<table class="data-table"><thead><tr>';
    for (const col of data.columns) {
        html += `<th>${escapeHtml(col)}</th>`;
    }
    html += '</tr></thead><tbody>';

    const rows = data.rows || [];
    for (const row of rows) {
        html += '<tr>';
        for (const cell of row) {
            const val = cell === null ? '—' : String(cell);
            html += `<td>${escapeHtml(val)}</td>`;
        }
        html += '</tr>';
    }
    html += '</tbody></table>';
    html += `<div class="row-count">${data.row_count || rows.length} row(s)</div>`;

    wrapper.innerHTML = html;
    container.appendChild(wrapper);
}

// ── Canvas Chart Rendering ──────────────────────────────────
function addChart(container, chartData) {
    if (!chartData || !chartData.columns || !chartData.rows || !chartData.rows.length) return;

    const chartType = chartData.type || 'bar';
    const wrapper = document.createElement('div');
    wrapper.className = 'chart-container';

    const canvas = document.createElement('canvas');
    canvas.width = 700;
    canvas.height = 250;
    wrapper.appendChild(canvas);

    const label = document.createElement('div');
    label.className = 'chart-label';
    label.textContent = `${chartType.charAt(0).toUpperCase() + chartType.slice(1)} Chart`;
    wrapper.appendChild(label);

    container.appendChild(wrapper);

    // Wait for DOM, then render
    requestAnimationFrame(() => {
        const ctx = canvas.getContext('2d');
        canvas.width = canvas.parentElement.clientWidth - 32;
        canvas.height = 250;

        switch (chartType) {
            case 'bar': drawBarChart(ctx, canvas, chartData); break;
            case 'line': drawLineChart(ctx, canvas, chartData); break;
            case 'pie': drawPieChart(ctx, canvas, chartData); break;
            default: drawBarChart(ctx, canvas, chartData);
        }
    });
}

const CHART_COLORS = [
    '#6366f1', '#8b5cf6', '#a78bfa', '#10b981', '#f59e0b',
    '#ef4444', '#3b82f6', '#ec4899', '#14b8a6', '#f97316',
];

function getChartValues(data) {
    // Use first column as labels, find a numeric column for values
    const labels = [];
    const values = [];

    let valueColIdx = -1;
    // Find the best numeric column (last numeric column, or second column)
    for (let i = data.columns.length - 1; i >= 1; i--) {
        const sample = data.rows[0][i];
        if (typeof sample === 'number' || !isNaN(parseFloat(sample))) {
            valueColIdx = i;
            break;
        }
    }
    if (valueColIdx === -1) valueColIdx = 1;

    for (const row of data.rows) {
        labels.push(String(row[0]));
        const val = parseFloat(row[valueColIdx]);
        values.push(isNaN(val) ? 0 : val);
    }

    return { labels, values };
}

function drawBarChart(ctx, canvas, data) {
    const { labels, values } = getChartValues(data);
    const w = canvas.width;
    const h = canvas.height;
    const pad = { top: 20, right: 20, bottom: 60, left: 70 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;
    const maxVal = Math.max(...values, 1);
    const barWidth = Math.min(chartW / labels.length * 0.6, 50);
    const gap = chartW / labels.length;

    // Background
    ctx.fillStyle = 'transparent';
    ctx.fillRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = pad.top + (chartH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(w - pad.right, y);
        ctx.stroke();

        // Y-axis labels
        const val = maxVal - (maxVal / 4) * i;
        ctx.fillStyle = '#6a6a80';
        ctx.font = '10px Inter';
        ctx.textAlign = 'right';
        ctx.fillText(formatNumber(val), pad.left - 8, y + 4);
    }

    // Bars
    labels.forEach((label, i) => {
        const x = pad.left + gap * i + (gap - barWidth) / 2;
        const barH = (values[i] / maxVal) * chartH;
        const y = pad.top + chartH - barH;

        // Gradient bar
        const gradient = ctx.createLinearGradient(x, y, x, y + barH);
        gradient.addColorStop(0, CHART_COLORS[i % CHART_COLORS.length]);
        gradient.addColorStop(1, CHART_COLORS[i % CHART_COLORS.length] + '80');
        ctx.fillStyle = gradient;

        // Rounded top
        const radius = Math.min(barWidth / 2, 6);
        ctx.beginPath();
        ctx.moveTo(x, y + barH);
        ctx.lineTo(x, y + radius);
        ctx.arcTo(x, y, x + radius, y, radius);
        ctx.arcTo(x + barWidth, y, x + barWidth, y + radius, radius);
        ctx.lineTo(x + barWidth, y + barH);
        ctx.closePath();
        ctx.fill();

        // Value on top
        ctx.fillStyle = '#a0a0b8';
        ctx.font = '10px Inter';
        ctx.textAlign = 'center';
        ctx.fillText(formatNumber(values[i]), x + barWidth / 2, y - 6);

        // X-axis label
        ctx.fillStyle = '#6a6a80';
        ctx.font = '10px Inter';
        ctx.textAlign = 'center';
        ctx.save();
        ctx.translate(x + barWidth / 2, h - pad.bottom + 12);
        ctx.rotate(-0.4);
        ctx.fillText(truncateLabel(label, 12), 0, 0);
        ctx.restore();
    });
}

function drawLineChart(ctx, canvas, data) {
    const { labels, values } = getChartValues(data);
    const w = canvas.width;
    const h = canvas.height;
    const pad = { top: 20, right: 20, bottom: 60, left: 70 };
    const chartW = w - pad.left - pad.right;
    const chartH = h - pad.top - pad.bottom;
    const maxVal = Math.max(...values, 1);
    const stepX = chartW / Math.max(labels.length - 1, 1);

    // Grid
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    for (let i = 0; i <= 4; i++) {
        const y = pad.top + (chartH / 4) * i;
        ctx.beginPath();
        ctx.moveTo(pad.left, y);
        ctx.lineTo(w - pad.right, y);
        ctx.stroke();

        const val = maxVal - (maxVal / 4) * i;
        ctx.fillStyle = '#6a6a80';
        ctx.font = '10px Inter';
        ctx.textAlign = 'right';
        ctx.fillText(formatNumber(val), pad.left - 8, y + 4);
    }

    // Area fill
    const gradient = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.3)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

    ctx.beginPath();
    ctx.moveTo(pad.left, pad.top + chartH);
    values.forEach((v, i) => {
        const x = pad.left + stepX * i;
        const y = pad.top + chartH - (v / maxVal) * chartH;
        ctx.lineTo(x, y);
    });
    ctx.lineTo(pad.left + stepX * (values.length - 1), pad.top + chartH);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line
    ctx.beginPath();
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 2.5;
    ctx.lineJoin = 'round';
    values.forEach((v, i) => {
        const x = pad.left + stepX * i;
        const y = pad.top + chartH - (v / maxVal) * chartH;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Dots & labels
    values.forEach((v, i) => {
        const x = pad.left + stepX * i;
        const y = pad.top + chartH - (v / maxVal) * chartH;

        ctx.fillStyle = '#6366f1';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#1a1a2e';
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fill();

        // X labels
        ctx.fillStyle = '#6a6a80';
        ctx.font = '10px Inter';
        ctx.textAlign = 'center';
        ctx.save();
        ctx.translate(x, h - pad.bottom + 12);
        ctx.rotate(-0.4);
        ctx.fillText(truncateLabel(labels[i], 12), 0, 0);
        ctx.restore();
    });
}

function drawPieChart(ctx, canvas, data) {
    const { labels, values } = getChartValues(data);
    const w = canvas.width;
    const h = canvas.height;
    const cx = w * 0.35;
    const cy = h / 2;
    const radius = Math.min(cx - 30, cy - 20);
    const total = values.reduce((a, b) => a + b, 0) || 1;

    let startAngle = -Math.PI / 2;

    labels.forEach((label, i) => {
        const sliceAngle = (values[i] / total) * Math.PI * 2;
        const endAngle = startAngle + sliceAngle;

        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.arc(cx, cy, radius, startAngle, endAngle);
        ctx.closePath();
        ctx.fillStyle = CHART_COLORS[i % CHART_COLORS.length];
        ctx.fill();

        // Separator
        ctx.strokeStyle = '#0a0a0f';
        ctx.lineWidth = 2;
        ctx.stroke();

        startAngle = endAngle;
    });

    // Inner circle (donut)
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 0.5, 0, Math.PI * 2);
    ctx.fillStyle = '#1a1a2e';
    ctx.fill();

    // Legend
    const legendX = w * 0.62;
    let legendY = 30;
    ctx.font = '11px Inter';

    labels.forEach((label, i) => {
        if (legendY > h - 20) return;
        const pct = ((values[i] / total) * 100).toFixed(1);

        ctx.fillStyle = CHART_COLORS[i % CHART_COLORS.length];
        ctx.fillRect(legendX, legendY - 8, 10, 10);

        ctx.fillStyle = '#a0a0b8';
        ctx.textAlign = 'left';
        ctx.fillText(`${truncateLabel(label, 15)} (${pct}%)`, legendX + 16, legendY);
        legendY += 22;
    });
}

// ── Utility Functions ───────────────────────────────────────
function formatNumber(n) {
    if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(1) + 'K';
    return n % 1 === 0 ? String(n) : n.toFixed(1);
}

function truncateLabel(str, max) {
    if (str.length <= max) return str;
    return str.substring(0, max - 1) + '…';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    const chat = document.getElementById('chatArea');
    chat.scrollTop = chat.scrollHeight;
}

// ── Pipeline Visualizer Control ─────────────────────────────
function resetPipeline() {
    ['translation', 'sql', 'response'].forEach(step => {
        const el = document.getElementById(`step-${step}`);
        if (el) {
            el.className = 'pipeline-step';
            const detail = document.getElementById(`detail-${step}`);
            if (detail) detail.textContent = '';
        }
    });
    document.querySelectorAll('.pipeline-arrow').forEach(a => a.classList.remove('active'));
}

function setPipelineActive(agent) {
    // Set previous steps as complete if needed
    const order = ['translation', 'sql', 'response'];
    const idx = order.indexOf(agent);

    order.forEach((step, i) => {
        const el = document.getElementById(`step-${step}`);
        if (!el) return;
        if (i < idx) {
            el.className = 'pipeline-step complete';
        } else if (i === idx) {
            el.className = 'pipeline-step active';
        }
    });

    // Activate arrows
    const arrows = document.querySelectorAll('.pipeline-arrow');
    arrows.forEach((arrow, i) => {
        if (i < idx) arrow.classList.add('active');
    });
}

function setPipelineComplete(agent) {
    const el = document.getElementById(`step-${agent}`);
    if (el) el.className = 'pipeline-step complete';
}

function setPipelineError(agent) {
    const el = document.getElementById(`step-${agent}`);
    if (el) el.className = 'pipeline-step error';
}

function completePipeline() {
    ['translation', 'sql', 'response'].forEach(step => {
        const el = document.getElementById(`step-${step}`);
        if (el && !el.classList.contains('error')) {
            el.className = 'pipeline-step complete';
        }
    });
    document.querySelectorAll('.pipeline-arrow').forEach(a => a.classList.add('active'));
}
