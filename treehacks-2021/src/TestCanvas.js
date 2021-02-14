import React, { Component } from "react";
import ReactDOM from "react-dom";
import * as THREE from 'three';
import {OrbitControls} from "three/examples/jsm/controls/OrbitControls";
import {OBJLoader} from "three/examples/jsm/loaders/OBJLoader";

const style = {
    height: 500 // we can control scene size by setting container dimensions
};

class App extends Component {
    componentDidMount() {
        this.sceneSetup();
        this.addLights();
        this.loadTheModel();
        this.startAnimationLoop();
        window.addEventListener('resize', this.handleWindowResize);
    }

    componentWillUnmount() {
        window.removeEventListener('resize', this.handleWindowResize);
        window.cancelAnimationFrame(this.requestID);
        this.controls.dispose();
    }

    // Standard scene setup in Three.js. Check "Creating a scene" manual for more information
    // https://threejs.org/docs/#manual/en/introduction/Creating-a-scene
    sceneSetup = () => {
        // get container dimensions and use them for scene sizing
        const width = this.mount.clientWidth / 1.5;
        const height = this.mount.clientHeight / 1.5;

        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(
            40, // fov = field of view
            width / height, // aspect ratio
            0.1, // near plane
            1000 // far plane
        );
        
        // Optional: set camera rotation
//         this.camera.rotation.y = 45/180 * Math.PI;
//         this.camera.rotation.x = 0;
//         this.camera.rotation.y = 0;
//         this.camera.rotation.z = 0;
        
        
        this.camera.position.z = 50;
        this.camera.position.x = 30; // set to 100 for perfect alignment
        this.camera.position.y = 30;
//         this.camera.position.z = -40; // is used here to set some distance from a cube that is located at z = 0
        
        // OrbitControls allow a camera to orbit around the object
        // https://threejs.org/docs/#examples/controls/OrbitControls
        this.controls = new OrbitControls( this.camera, this.mount );

        
        this.renderer = new THREE.WebGLRenderer();
        this.renderer.setSize( width, height );
        this.mount.appendChild( this.renderer.domElement ); // mount using React ref
    };

    
    loadTheModel = () => { // Taken from Three.js OBJ Loader example (https://threejs.org/docs/#examples/en/loaders/OBJLoader)
        
        // instantiate a loader
        const loader = new OBJLoader();
        const face = loader.parse(this.props.faceObj);
        this.scene.add( face );

        // Rotate face by <x> radians
        face.rotation.x = 5/180 * Math.PI;
        face.rotation.y = 5/180 * Math.PI;
        face.rotation.z = 0/180 * Math.PI;
        
        
        // Optional: change some custom props of the element: 
        // placement, color, rotation, anything that should be
        // done once the model was loaded and ready for displays
    };

    // adding some lights to the scene
    addLights = () => {
        const lights = [];

        // set color and intensity of lights
        lights[ 0 ] = new THREE.PointLight( 0xffffff, .2, 0 );
        lights[ 1 ] = new THREE.PointLight( 0xffffff, .3, 0 );
        lights[ 2 ] = new THREE.PointLight( 0xffffff, .4, 0 );
        lights[3] = new THREE.AmbientLight(0x8d5524);
//         lights[3] = new THREE.AmbientLight(0x592f2a);

        // place some lights around the scene for best looks and feel
        lights[ 0 ].position.set( 0, 2000, 0 );
        lights[ 1 ].position.set( 1000, 2000, 1000 );
        lights[ 2 ].position.set( - 1000, - 2000, - 1000 );
        lights[3].position.set(2000, 2000, 2000);

        this.scene.add( lights[ 0 ] );
        this.scene.add( lights[ 1 ] );
        this.scene.add( lights[ 2 ] );
        this.scene.add( lights[ 3 ] );
    };

    startAnimationLoop = () => {
        this.renderer.render( this.scene, this.camera ); 
        
        
        // The window.requestAnimationFrame() method tells the browser that you wish to perform
        // an animation and requests that the browser call a specified function
        // to update an animation before the next repaint
        this.requestID = window.requestAnimationFrame(this.startAnimationLoop);
    };

    handleWindowResize = () => {
        const width = this.mount.clientWidth;
        const height = this.mount.clientHeight;

        this.renderer.setSize( width, height );
        this.camera.aspect = width / height;

        // Note that after making changes to most of camera properties you have to call
        // .updateProjectionMatrix for the changes to take effect.
        this.camera.updateProjectionMatrix();
    };

    render() {
        return <div style={style} ref={ref => (this.mount = ref)} />;
    }
}

class Container extends React.Component {
    state = {isMounted: true};

    render() {
        const {isMounted = true, loadingPercentage = 0} = this.state;
        return (
            <>
                <button onClick={() => this.setState(state => ({isMounted: !state.isMounted}))}>
                    {isMounted ? "Unmount" : "Mount"}
                </button>
                {this.props.faceObj && <App faceObj={this.props.faceObj} onProgress={loadingPercentage => this.setState({ loadingPercentage })} />}
                {isMounted && loadingPercentage === 100 && <div>Scroll to zoom, drag to rotate</div>}
                {isMounted && loadingPercentage !== 100 && <div>Loading Model: {loadingPercentage}%</div>}
            </>
        )
    }
}

export default Container;