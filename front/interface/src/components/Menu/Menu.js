import React, {Component} from 'react';
import {Navbar, Nav, NavDropdown, Badge} from "react-bootstrap";
import './Menu.css';
import Current from '../Current/Current.js';
import SpecificMarket from "../SpecificMarket/SpecificMarket";
import Historical from "../Historical/Historical";
import axios from "axios";
import {Redirect} from "react-router-dom";

class Menu extends Component {

    constructor(props) {
        super(props);
        this.state = {
            "required_service": 0,
            "active_markets": [],
            "current_markets" : [],
            "flag_url" : "https://www.countryflags.io/",
            "concerned_market" : ""
        };
        this.r = axios.create();
        this.r.defaults.baseURL = "http://localhost:8000/api";
        console.log(localStorage.getItem("token"));
        this.r.defaults.headers['Access-Control-Allow-Headers'] = 'x-access-token'
        this.r.defaults.headers['x-access-token'] = localStorage.getItem("token")

    }


    componentDidMount() {
        this.r.get('/all_markets/')
                .then(
                    response => {
                        console.log(response.data);
                    this.setState({
                        "active_markets" : response.data
                    })
                    }
                )
                .catch(
                    _ => {
                        window.location = window.location.origin
                    }
                    );


        this.r.get("/current/")
            .then(
                response => {
                    this.setState({
                        "current_markets" : response.data
                    })
                }
            )
            .catch(
                _ => {window.location = window.location.origin}
            )


        };

     get_markets = () =>{
        if (this.state.active_markets.length !== 0){
            return ( this.state.active_markets.map(
                                    elt => (
                                        <NavDropdown.Item>
                                            <div className={"row"}>
                                                <div className={"col"} onClick={event => {
                                                    this.close_nav();
                                                    this.setState({
                                                        "required_service": 2,
                                                        "concerned_market" : elt
                                                    })}}>{elt}</div>
                                                <div className="col text-right">
                                                    <img alt= "" src={this.state.flag_url+elt.substring(0,2)+"/flat/32.png"}/> /
                                                    <img alt="" src={this.state.flag_url+elt.substring(3,5)+"/flat/32.png"}/>
                                                </div>
                                            </div>
                                            <NavDropdown.Divider/>

                                        </NavDropdown.Item>
                                    )));
        }
        else {
            return(<NavDropdown.Item>Oops no market was found :(</NavDropdown.Item>)
        }
    };

     menu_print = () => {
         switch(this.state.required_service) {
             case 0:
                 return (
                     <div className={"contentMenu"}>
                         <Current className={"contentMenu"} data={this.state.current_markets}/>
                     </div>);
             case 1:
                 return(
                 <div className={"contentMenu"}>
                    <Historical endpoint={this.r}/>;
                 </div>
                 );
             case 2:
                 return (
                     <div className={"contentMenu"}>
                     <SpecificMarket  concerned={this.state.concerned_market}
                                                      img={this.state.flag_url} endpoint={this.r}/>
                     </div>);

         }
     };


     close_nav = () => ( document.getElementsByTagName("button")[0].click() );

     error_display = () => this.error ? <Redirect to={"/"}/> : null;

     render() {
        return (
            <div>
                {this.error_display()}
                <Navbar collapseOnSelect expand="sm" bg="dark" variant="dark" >
                    <Navbar.Brand>STEA</Navbar.Brand>
                    <Navbar.Toggle aria-controls="responsive-navbar-nav"/>
                    <Navbar.Collapse id="responsive-navbar-nav">
                        <Nav className="mr-auto">
                            <Nav.Link onClick={() => {
                                this.close_nav();
                                this.setState({
                                "required_service":0
                            })
                            }}>
                                <span className={"textInfo"}> Current Positions </span>
                                <Badge variant="light">{this.state.current_markets.length}</Badge>
                            </Nav.Link>
                            <Nav.Link onClick={() =>{
                                this.close_nav();
                                this.setState({"required_service":1})}}>
                                <span className={"textInfo"}> Historical (Last 30 Positions) </span>
                            </Nav.Link>
                            <NavDropdown title="Specific Market" id="basic-nav-dropdown">
                                {this.get_markets()}
                            </NavDropdown>

                        </Nav>
                    </Navbar.Collapse>
                </Navbar>
                {this.menu_print()}
            </div>
        );
    }
}
export default Menu;