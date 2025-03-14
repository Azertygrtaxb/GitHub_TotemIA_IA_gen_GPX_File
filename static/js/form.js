document.getElementById('routeForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const statusMessage = document.getElementById('statusMessage');
    const submitButton = e.target.querySelector('button[type="submit"]');

    // Collect form data
    const formData = {
        location: document.getElementById('location').value,
        activity_type: document.getElementById('activity_type').value,
        level: document.getElementById('level').value,
        distance: document.getElementById('distance').value,
        landscape: document.getElementById('landscape').value,
        route_type: document.getElementById('route_type').value,
        elevation_preference: document.getElementById('elevation_preference').value,
        duration: document.getElementById('duration').value,
        surface_type: document.getElementById('surface_type').value,
        points_of_interest: document.getElementById('points_of_interest').value,
        email: document.getElementById('email').value
    };

    try {
        // Disable submit button and show loading state
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';

        statusMessage.className = 'alert alert-info mt-3';
        statusMessage.style.display = 'block';
        statusMessage.textContent = 'Generating your route...';

        const response = await fetch('/generate-route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            statusMessage.className = 'alert alert-success mt-3';
            statusMessage.textContent = 'Route generated successfully! Check your email.';
        } else {
            throw new Error(data.error || 'Failed to generate route');
        }
    } catch (error) {
        statusMessage.className = 'alert alert-danger mt-3';
        statusMessage.textContent = error.message;
    } finally {
        // Re-enable submit button
        submitButton.disabled = false;
        submitButton.textContent = 'Generate Route';
    }
});