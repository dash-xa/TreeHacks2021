import React, { useState, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';

import AppCanvas from './AppCanvas';
import TestCanvas from './TestCanvas';

import './App.css';

function App() {

  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState();
    
  const [retrievedObjFile, setRetrievedObj] = useState();

  const capture = useCallback(
    () => {
      const imageSrc = webcamRef.current.getScreenshot();
      console.log(imageSrc);
      setCapturedImage(imageSrc);
    },
    [webcamRef]
  );

  const sendToServer = () => {
    fetch('https://maskfit.verafy.me/api/generate', {
      method: 'POST',
      headers: {
        'Accept': 'image/jpeg',
        'Content-Type': 'image/jpeg',
      },
      body: capturedImage,
    }).then(
      (response) => response.text())
      .then((response) => {
        const objFile = response;
        console.log(objFile);
        setRetrievedObj(objFile);
      }
    )
  }
  

  return (
    <div className='main'>
      <h1>test</h1>
      <TestCanvas faceObj={retrievedObjFile} />
      <Webcam 
        className="mirrorX"
        audio={false}
        ref={webcamRef}
        screenshotFormat="image/jpeg"
      />
      <div>
        <button onClick={capture}>Capture photo</button>

        <button onClick={sendToServer}>Send</button>
      </div>
    </div>
  );
}

export default App;
