document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('prediction-form');
    const submitBtnSpan = form.querySelector('.btn-submit span');
    const spinner = document.getElementById('btn-spinner');
    
    const emptyState = document.getElementById('empty-state');
    const predictionContent = document.getElementById('prediction-content');
    const severityBox = document.getElementById('severity-box');
    const severityValue = document.getElementById('severity-value');
    const actionRecommendation = document.getElementById('action-recommendation');
    const blackspotAlert = document.getElementById('blackspot-alert');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // UI Loading state
        submitBtnSpan.textContent = 'Analyzing...';
        spinner.style.display = 'block';

        // Gather form data
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        // Convert string values to numbers
        for (let key in data) {
            data[key] = Number(data[key]);
        }

        try {
            // Artificial delay to show the loading animation for premium feel
            await new Promise(r => setTimeout(r, 600));

            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (result.success) {
                // Hide empty state, show results
                emptyState.style.display = 'none';
                predictionContent.style.display = 'block';

                // Update Severity
                const severity = result.severity;
                severityValue.textContent = severity;
                
                // Reset classes
                severityBox.className = 'severity-box';
                
                // Apply dynamic styles based on severity
                if (severity === 'Fatal') {
                    severityBox.classList.add('fatal');
                    actionRecommendation.innerHTML = '<span style="color:var(--danger-red)">CRITICAL: Dispatch emergency units immediately and divert traffic.</span>';
                } else if (severity === 'Serious') {
                    severityBox.classList.add('serious');
                    actionRecommendation.innerHTML = '<span style="color:var(--warning-yellow)">WARNING: Prepare medical units and issue route caution.</span>';
                } else {
                    severityBox.classList.add('slight');
                    actionRecommendation.innerHTML = '<span style="color:var(--success-green)">Standard monitoring. No immediate escalation needed.</span>';
                }

                // Update Blackspot Alert
                if (result.is_blackspot) {
                    blackspotAlert.style.display = 'flex';
                } else {
                    blackspotAlert.style.display = 'none';
                }

            } else {
                alert('Error predicting severity: ' + result.error);
            }

        } catch (error) {
            console.error('Error:', error);
            alert('Failed to connect to the prediction server.');
        } finally {
            // Reset UI Loading state
            submitBtnSpan.textContent = 'Analyze Risk';
            spinner.style.display = 'none';
        }
    });
});
