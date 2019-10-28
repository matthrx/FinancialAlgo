import React, {Component} from 'react';
import {Navbar, Nav, NavDropdown, Badge} from "react-bootstrap";
import './Menu.css';


class Menu extends Component {

    constructor(props) {
        super(props);
        this.state = {
            "required_service": 0,
            "active_markets": [],
            "current_markets" : [],
            "flag_url" : "https://www.countryflags.io/"
        };
    }


    componentDidMount() {
        this.props.endpoint.get('/all_markets/')
                .then(
                    response => {
                        console.log(response.data);
                    this.setState({
                        "active_markets" : response.data
                    })
                    }
                )
                .catch(
                    (err) => {
                        console.error(err)
                    }
                );

        this.props.endpoint.get("/current/")
            .then(
                response => {
                    this.setState({
                        "current_markets" : response.data
                    })
                }
            )
            .catch(
                err => {
                    console.log(err);
                }
            )


        };

     get_markets = () =>{
        if (this.state.active_markets.length !== 0){
            return ( this.state.active_markets.map(
                                    elt => (
                                        <NavDropdown.Item>
                                            <div className={"row"}>
                                                <div className={"col"}>{elt}</div>
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

    render() {

        return (
            <Navbar collapseOnSelect expand="sm" bg="dark" variant="dark" fixed="top">
                <Navbar.Brand>STEA</Navbar.Brand>
                <Navbar.Toggle aria-controls="responsive-navbar-nav"/>
                <Navbar.Collapse id="responsive-navbar-nav">
                    <Nav className="mr-auto">
                        <Nav.Link onClick={() => this.setState({
                            "required_service":0
                        })
                        }>
                            <span className={"textInfo"}> Current Positions </span>
                            <Badge variant="light">{this.state.current_markets.length}</Badge>
                        </Nav.Link>
                        <Nav.Link onClick={() =>{this.setState({"required_service":1})}}>
                            <span className={"textInfo"}> Historical </span>
                        </Nav.Link>
                        <NavDropdown title="Specific Market" id="basic-nav-dropdown">
                            {this.get_markets()}
                        </NavDropdown>

                    </Nav>
                </Navbar.Collapse>
            </Navbar>
        );
    }
}
export default Menu;