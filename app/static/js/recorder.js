// app/static/js/recorder.js
let mediaRecorder, chunks = [];

async function startRecording() {
  if (!navigator.mediaDevices) {
    alert("No mediaDevices API available in this browser.");
    return;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  chunks = [];
  mediaRecorder.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
  mediaRecorder.start();
}

function stopRecording() {
  return new Promise((resolve, reject) => {
    if (!mediaRecorder) { resolve(null); return; }
    mediaRecorder.onstop = () => {
      const blob = new Blob(chunks, { type: 'audio/webm' });
      resolve(blob);
    };
    mediaRecorder.stop();
  });
}
