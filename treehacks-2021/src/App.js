import React, { useState, useEffect, useRef, useCallback } from 'react';
import Webcam from 'react-webcam';

import AppCanvas from './AppCanvas2';
import TestCanvas from './TestCanvas';
import default_obj from './default_obj';

import './App.css';


function useWindowSize() {
  // Initialize state with undefined width/height so server and client renders match
  // Learn more here: https://joshwcomeau.com/react/the-perils-of-rehydration/
  const [windowSize, setWindowSize] = useState({
    width: undefined,
    height: undefined,
  });

  useEffect(() => {
    // Handler to call on window resize
    function handleResize() {
      // Set window width/height to state
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    }
    
    // Add event listener
    window.addEventListener("resize", handleResize);
    
    // Call handler right away so state gets updated with initial window size
    handleResize();
    
    // Remove event listener on cleanup
    return () => window.removeEventListener("resize", handleResize);
  }, []); // Empty array ensures that effect is only run on mount

  return windowSize;
}


function App() {

  const webcamRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState();
  const [useAR, setUseAR] = useState(0);
  const [sentStatus, setSentStatus] = useState("Hit the Capture Image button to take a photo of our face!");
  console.log("SENT STATUS", sentStatus);
    
  const [retrievedObjFile, setRetrievedObj] = useState();
    
  const [retrievedMaskOnly, setRetrievedMask] = useState();
    
  const size = useWindowSize();
  const constraints = {
      width: size.width / 2,
      height: size.height / 2,
  }

  const capture = useCallback(
    () => {
      const imageSrc = webcamRef.current.getScreenshot();
      console.log(imageSrc);
      setCapturedImage(imageSrc);
    },
    [webcamRef]
  );
    
    

  const sendToServer = () => {
    fetch('https://maskfit.verafy.me/api/generate_facemask_fit', {
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
        console.log("OTHER MASK");
        setRetrievedObj(objFile);
        setSentStatus('Your mask was retrieved successfully! To see how it looks and download it, click the button below!');
      }
    )
  }
  
  const sendAnotherToServer = () => {
    fetch('https://maskfit.verafy.me/api/generate_facemask', {
      method: 'POST',
      headers: {
        'Accept': 'image/jpeg',
        'Content-Type': 'image/jpeg',
      },
      body: capturedImage,
    }).then((response) => {
        if (response.status == 500) {
            setSentStatus('Your mask was retrieved successfully! To see how it looks and download it, click the button below!\n\nMask fitting had an error - a default mask frame is loaded below');
            return default_obj;
        }
        return response.text()
    }).then((response) => {
        const objFile = response;
        console.log("RETRIEVING MY MASK");
        setRetrievedMask(objFile);
      }
    )
  }
  
  const downloadTxtFile = () => {
    const element = document.createElement("a");
    const file = new Blob([retrievedMaskOnly], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = "generated_mask.obj";
    document.body.appendChild(element); // Required for this to work in FireFox
    element.click();
  }
    

  return (
    <div className='main' onClick={() => {
        console.log("THING");
        if (useAR > 1) setUseAR(0);
        else if (useAR == 0) {}
        else setUseAR(useAR + 1);
  }}>
      <div className='diag-banner'>
        <p className='title-banner'>Maskus</p>
      </div>
      <div className='bordered-screen'>
          <Webcam 
            className="mirrorX"
            audio={false}
            ref={webcamRef}
            screenshotFormat="image/jpeg"
            videoConstraints={constraints}
          />
          <div style={{paddingTop: '1rem'}}>
            <button onClick={() => {
                capture();
                setSentStatus('Now, hit the Send button to ship that image to our servers!')
            }}>Capture photo</button>
            <button onClick={() => {
                sendToServer();
                setSentStatus('Image sent, please wait...');
            }}>Send</button>
          </div>
          <div>
            <div>
                {sentStatus && <p>{sentStatus}</p>}
            </div>
            <div>
                <button onClick={() => {
                    if (!retrievedMaskOnly) {
                        sendAnotherToServer();
                    }
                    console.log("OTHER THING")
                    setUseAR(useAR + 1);
                }}>AR Mode + Load Mask</button>
                {retrievedMaskOnly ? <button onClick={() => {
                                        downloadTxtFile();
                                    }}>Download Mask</button> : null}
            </div>
          </div>
      </div>
      <div className='bordered-screen'>
        <TestCanvas faceObj={retrievedObjFile} />
      </div>
      {useAR ? <div className='dim' onClick={() => {
          console.log("TESTING CLICK")
      }}> </div> : null }
      <AppCanvas maskfile={retrievedMaskOnly} hide={useAR ? 'visible' : 'hidden'} />
      
    </div>
  );
}

export default App;
