const alertSound = new Audio('/static/assets/alert.mp3');

setInterval(async () => {
    try {
        const response = await fetch('/get_alerts');
        const data = await response.json();
        const logBox = document.getElementById('event-logs');

        if (data.alerts && data.alerts.length > 0) {
            // Sound Fix: Reset and Play
            alertSound.pause();
            alertSound.currentTime = 0; 
            alertSound.play().catch(e => console.log("Click page to enable audio"));
            
            data.alerts.forEach(msg => {
                const div = document.createElement('div');
                div.className = 'alert-item';
                div.innerHTML = `<strong>[${new Date().toLocaleTimeString()}]</strong> ${msg}`;
                logBox.prepend(div);
            });
        }
    } catch (err) {
        console.log("Fetch error");
    }
}, 1000);