// Form validation and handling
document.addEventListener('DOMContentLoaded', function() {
    const predictionForm = document.getElementById('predictionForm');
    
    if (predictionForm) {
        predictionForm.addEventListener('submit', function(e) {
            const inputs = predictionForm.querySelectorAll('input[type="number"]');
            let isValid = true;
            
            inputs.forEach(input => {
                const value = parseFloat(input.value);
                
                if (input.name === 'soil_ph') {
                    if (value < 0 || value > 14) {
                        alert('Soil pH must be between 0 and 14');
                        isValid = false;
                        e.preventDefault();
                    }
                }
                
                if (input.name === 'humidity') {
                    if (value < 0 || value > 100) {
                        alert('Humidity must be between 0 and 100%');
                        isValid = false;
                        e.preventDefault();
                    }
                }
                
                if (value < 0) {
                    alert(`${input.name.charAt(0).toUpperCase() + input.name.slice(1)} cannot be negative`);
                    isValid = false;
                    e.preventDefault();
                }
            });
            
            if (isValid) {
                // Show loading state
                const submitBtn = predictionForm.querySelector('button[type="submit"]');
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
                submitBtn.disabled = true;
            }
        });
    }
});

// Add smooth scrolling
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});
