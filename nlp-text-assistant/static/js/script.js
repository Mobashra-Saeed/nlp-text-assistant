document.addEventListener('DOMContentLoaded', () => {
    const editor = document.getElementById('editor-canvas');
    const popover = document.getElementById('suggestion-popover');
    const popoverMessage = document.getElementById('popover-message');
    const popoverType = document.getElementById('popover-type');
    const chipsList = document.getElementById('chips-list');
    const popoverClose = document.getElementById('popover-close');
    const statusIndicator = document.getElementById('status-indicator');

    const btnEditor = document.getElementById('btn-editor-view');
    const btnBenchmark = document.getElementById('btn-benchmark-view');
    const editorView = document.getElementById('editor-view');
    const benchmarkView = document.getElementById('benchmark-view');
    const runBenchmarkBtn = document.getElementById('run-benchmark-btn');

    let debounceTimer = null;
    let activeTargetSpan = null;

    // View Navigation
    btnEditor.addEventListener('click', () => {
        btnEditor.classList.add('active');
        btnBenchmark.classList.remove('active');
        editorView.classList.add('active');
        benchmarkView.classList.remove('active');
    });

    btnBenchmark.addEventListener('click', () => {
        btnBenchmark.classList.add('active');
        btnEditor.classList.remove('active');
        benchmarkView.classList.add('active');
        editorView.classList.remove('active');
    });

    // 400ms Debouncing Logic
    editor.addEventListener('input', () => {
        statusIndicator.innerHTML = '<span class="pulse-dot" style="background:#f59e0b"></span> Checking...';
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            analyzeText();
        }, 400);
    });

    async function analyzeText() {
        const rawText = editor.innerText;
        if (!rawText.trim()) {
            statusIndicator.innerHTML = '<span class="pulse-dot"></span> Ready';
            return;
        }

        try {
            const response = await fetch('/api/check-text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: rawText })
            });

            const data = await response.json();
            if (editor.innerText !== rawText) {
                return;
            }
            renderHighlights(rawText, data.matches);
            statusIndicator.innerHTML = '<span class="pulse-dot"></span> Synced';
        } catch (err) {
            console.error('Error checking text:', err);
            statusIndicator.innerHTML = '<span class="pulse-dot" style="background:#ef4444"></span> Error';
        }
    }

    function renderHighlights(fullText, matches) {
        if (!matches || matches.length === 0) {
            return; // Don't replace HTML if no matches to preserve cursor location
        }

        let highlightedHTML = '';
        let lastIdx = 0;

        matches.forEach(match => {
            const start = match.offset;
            const end = match.offset + match.length;
            
            // Append clean text prior to error
            highlightedHTML += escapeHTML(fullText.substring(lastIdx, start));
            
            // Wrap error in marked span
            const cls = match.type === 'grammar' ? 'err-grammar' : 'err-spelling';
            const suggestionsData = encodeURIComponent(JSON.stringify(match.suggestions));
            
            highlightedHTML += `<span class="${cls}" data-msg="${escapeHTML(match.message)}" data-type="${match.type}" data-suggestions="${suggestionsData}">${escapeHTML(fullText.substring(start, end))}</span>`;
            
            lastIdx = end;
        });

        highlightedHTML += escapeHTML(fullText.substring(lastIdx));
        
        const savedSelection = getEditorSelection(editor);
        editor.innerHTML = highlightedHTML;
        restoreEditorSelection(editor, savedSelection);
        bindErrorSpanEvents();
    }

    function getEditorSelection(root) {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) return null;

        const range = selection.getRangeAt(0);
        if (!root.contains(range.startContainer) || !root.contains(range.endContainer)) return null;

        const getOffset = (node, nodeOffset) => {
            const prefix = document.createRange();
            prefix.selectNodeContents(root);
            prefix.setEnd(node, nodeOffset);
            return prefix.toString().length;
        };

        return {
            start: getOffset(range.startContainer, range.startOffset),
            end: getOffset(range.endContainer, range.endOffset)
        };
    }

    function restoreEditorSelection(root, savedSelection) {
        if (!savedSelection) return;

        const getTextPosition = (offset) => {
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
            let remaining = offset;
            let node;

            while ((node = walker.nextNode())) {
                if (remaining <= node.textContent.length) {
                    return { node, offset: remaining };
                }
                remaining -= node.textContent.length;
            }

            return { node: root, offset: root.childNodes.length };
        };

        const start = getTextPosition(savedSelection.start);
        const end = getTextPosition(savedSelection.end);
        const range = document.createRange();
        range.setStart(start.node, start.offset);
        range.setEnd(end.node, end.offset);

        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
    }

    function bindErrorSpanEvents() {
        document.querySelectorAll('.err-spelling, .err-grammar').forEach(span => {
            span.addEventListener('click', (e) => {
                e.stopPropagation();
                activeTargetSpan = span;
                
                const rect = span.getBoundingClientRect();
                const type = span.getAttribute('data-type');
                const msg = span.getAttribute('data-msg');
                const suggestions = JSON.parse(decodeURIComponent(span.getAttribute('data-suggestions')));

                popoverType.textContent = type;
                popoverType.className = `popover-badge ${type}`;
                popoverMessage.textContent = msg;

                chipsList.innerHTML = '';
                if (suggestions.length === 0) {
                    chipsList.innerHTML = '<span style="font-size:0.8rem; color:#94a3b8">No suggestions available</span>';
                } else {
                    suggestions.forEach(sug => {
                        const chip = document.createElement('button');
                        chip.type = 'button';
                        chip.className = 'chip';
                        chip.textContent = sug;
                        chip.addEventListener('click', () => applyCorrection(sug));
                        chipsList.appendChild(chip);
                    });
                }

                popover.style.top = `${rect.bottom + window.scrollY + 6}px`;
                popover.style.left = `${rect.left + window.scrollX}px`;
                popover.classList.remove('hidden');
            });
        });
    }

    function applyCorrection(replacement) {
        if (activeTargetSpan) {
            const textNode = document.createTextNode(replacement);
            activeTargetSpan.parentNode.replaceChild(textNode, activeTargetSpan);
            popover.classList.add('hidden');
            activeTargetSpan = null;

            const range = document.createRange();
            range.setStart(textNode, textNode.length);
            range.collapse(true);
            editor.focus();
            const selection = window.getSelection();
            selection.removeAllRanges();
            selection.addRange(range);
            analyzeText();
        }
    }

    popoverClose.addEventListener('click', () => popover.classList.add('hidden'));
    document.addEventListener('click', (e) => {
        if (!popover.contains(e.target)) popover.classList.add('hidden');
    });

    // Benchmark Execution
    runBenchmarkBtn.addEventListener('click', async () => {
        runBenchmarkBtn.disabled = true;
        runBenchmarkBtn.innerText = 'Evaluating...';

        try {
            const res = await fetch('/api/evaluate', { method: 'POST' });
            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.error || 'Benchmark evaluation failed');
            }

            document.getElementById('val-accuracy').textContent = (data.accuracy * 100).toFixed(1) + '%';
            document.getElementById('val-precision').textContent = (data.precision * 100).toFixed(1) + '%';
            document.getElementById('val-recall').textContent = (data.recall * 100).toFixed(1) + '%';
            document.getElementById('val-f1').textContent = (data.f1_score * 100).toFixed(1) + '%';

            document.getElementById('val-total').textContent = data.total_words;
            document.getElementById('val-tp').textContent = data.true_positives;
            document.getElementById('val-fp').textContent = data.false_positives;
            document.getElementById('val-fn').textContent = data.false_negatives;
            document.getElementById('val-tn').textContent = data.true_negatives;
            document.getElementById('val-top1').textContent = `${data.correct_top1} (${(data.correction_accuracy_top1 * 100).toFixed(1)}%)`;
            document.getElementById('val-top5').textContent = `${data.correct_top5} (${(data.correction_accuracy_top5 * 100).toFixed(1)}%)`;
            document.getElementById('val-time').textContent = data.execution_time_seconds + 's';

            const contextMetrics = data.context_benchmark;
            document.getElementById('context-val-passed').textContent = `${contextMetrics.true_positives + contextMetrics.true_negatives} / ${contextMetrics.total_cases}`;
            document.getElementById('context-val-tp').textContent = contextMetrics.true_positives;
            document.getElementById('context-val-fn').textContent = contextMetrics.false_negatives;
            document.getElementById('context-val-fp').textContent = contextMetrics.false_positives;
        } catch (err) {
            alert(`Error running benchmark evaluation: ${err.message}`);
        } finally {
            runBenchmarkBtn.disabled = false;
            runBenchmarkBtn.innerText = 'Run Model Evaluation';
        }
    });

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }
});