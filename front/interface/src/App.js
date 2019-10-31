import React, {Component} from 'react';
import logo from './logo.svg';
import './App.css';
import axios from 'axios';
import Authentication from "./components/Authentication/Authentication";

class App extends Component {

    render() {

        return (
            <div className="App">
                <Authentication endpoint={this.r}/>
            </div>
        );
    }
}

export default App;
