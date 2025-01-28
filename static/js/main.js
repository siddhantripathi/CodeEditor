let editor;

// Add this at the start of the file
function applyTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    return savedTheme;
}

// Theme switching functionality
function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle.querySelector('.icon');
    
    function updateThemeUI(theme) {
        if (theme === 'dark') {
            themeIcon.textContent = '🌞';
        } else {
            themeIcon.textContent = '🌙';
        }
        
        if (editor) {
            editor.setOption('theme', theme === 'dark' ? 'dracula' : 'default');
        }
    }
    
    // Set initial theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeUI(savedTheme);
    
    // Theme toggle handler
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeUI(newTheme);
    });
}

// Call this immediately
document.addEventListener('DOMContentLoaded', function() {
    applyTheme();
    initializeTheme();
    
    // Initialize CodeMirror
    const codeEditor = document.getElementById('code-editor');
    if (codeEditor) {
        const savedTheme = localStorage.getItem('theme') || 'light';
        editor = CodeMirror.fromTextArea(codeEditor, {
            mode: 'python',
            theme: savedTheme === 'dark' ? 'dracula' : 'default',
            lineNumbers: true,
            indentUnit: 4,
            autoCloseBrackets: true,
            matchBrackets: true,
            lineWrapping: true
        });

        document.getElementById('run-btn').addEventListener('click', runCode);
    }
});

function showNotification(message, isSuccess) {
    // Remove existing notification if any
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification ${isSuccess ? 'success' : 'error'}`;
    notification.innerHTML = `
        <span class="icon">${isSuccess ? '✓' : '✕'}</span>
        <span class="message">${message}</span>
    `;

    // Add to document
    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function runCode() {
    const code = editor.getValue();
    const outputElement = document.getElementById('output');
    const problemId = window.location.pathname.split('/').pop();
    const runBtn = document.getElementById('run-btn');
    
    // Disable button and show loading state
    runBtn.disabled = true;
    runBtn.textContent = 'Running...';
    
    fetch('/execute', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            code: code,
            problem_id: problemId
        })
    })
    .then(response => response.json())
    .then(data => {
        // Update output
        if (data.error) {
            outputElement.textContent = data.error;
            outputElement.className = 'error-output';
            showNotification('Code execution failed', false);
        } else {
            let output = '';
            if (data.test_results) {
                output = 'Test Results:\n\n';
                data.test_results.forEach((result, index) => {
                    output += `Test Case ${index + 1}: ${result.passed ? 'Passed ✓' : 'Failed ✕'}\n`;
                    if (!result.passed) {
                        output += `Expected: ${result.expected}\n`;
                        output += `Got: ${result.actual}\n`;
                    }
                    output += '\n';
                });
            }
            output += data.output || 'No output';
            
            outputElement.textContent = output;
            outputElement.className = '';
            
            const allTestsPassed = data.test_results && 
                                 data.test_results.every(r => r.passed);
            showNotification(allTestsPassed ? 'All tests passed!' : 'Some tests failed', allTestsPassed);
        }
    })
    .catch(error => {
        outputElement.textContent = 'Error: ' + error.message;
        outputElement.className = 'error-output';
        showNotification('Error executing code', false);
    })
    .finally(() => {
        // Re-enable button
        runBtn.disabled = false;
        runBtn.textContent = 'Run Code';
    });
} 