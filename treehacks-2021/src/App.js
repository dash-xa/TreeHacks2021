import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';

import './App.css'

function App() {

  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState();

  const capture = useCallback(
    () => {
      const imageSrc = webcamRef.current.getScreenshot();
      console.log(imageSrc);
      setCapturedImage(imageSrc);
    },
    [webcamRef]
  );

  const sendToServer = () => {
    fetch('http://35.188.28.21:8000/', {
      method: 'POST',
      headers: {
        'Accept': 'image/jpeg',
        'Content-Type': 'image/jpeg',
      },
      body: capturedImage,
    }).then(
      (response) => {
        console.log(response);
      }
    )
  }
  

  return (
    <div class='main'>
      <Webcam 
        className="mirrorX"
        audio={false}
        ref={webcamRef}
        screenshotFormat="image/jpeg"
      />
      <div>
        <button onClick={capture}>Capture photo</button>
        <button>
          <a download="webcam-image" href={capturedImage}>Download</a>
        </button>

        <button onClick={sendToServer}>Send</button>
      </div>
    </div>
  );
}

export default App;
