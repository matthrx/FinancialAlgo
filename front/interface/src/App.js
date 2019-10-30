import React, {Component} from 'react';
import logo from './logo.svg';
import './App.css';
import Menu from "./components/Menu/Menu";
import axios from 'axios';

class App extends Component {

    constructor(props) {
        super(props);
        this.r = axios.create();
        this.r.defaults.baseURL = "http://127.0.0.1:8000"

    }

    render() {

        return (
            <div className="App">
                <Menu endpoint={this.r}/>
            </div>
        );
    }
}

export default App;
