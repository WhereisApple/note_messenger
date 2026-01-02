async function createNote() {
    const text = document.getElementById("noteText").value;
    if (!text) {
        document.getElementById("otpResult").innerText = "Please type a note first!";
        return;
    }

    const res = await fetch("/api/notes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
    });

    const data = await res.json();
    if (res.ok) {
        document.getElementById("otpResult").innerText = "Your OTP: " + data.otp + " (expires in 5 minutes)";
        document.getElementById("noteText").value = "";
    } else {
        document.getElementById("otpResult").innerText = data.error;
    }
}

async function getNote() {
    const otp = document.getElementById("otpInput").value;
    if (!otp) {
        document.getElementById("noteOutput").innerText = "Please enter an OTP!";
        return;
    }

    const res = await fetch("/api/notes/retrieve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ otp })
    });

    const data = await res.json();
    if (res.ok) {
        document.getElementById("noteOutput").innerText = "Your Note: " + data.text;
        document.getElementById("otpInput").value = "";
    } else {
        document.getElementById("noteOutput").innerText = data.error;
    }
}
