import React, {Component} from "react"
import "./SpecificMarket.css"
import anime from "animejs"
import {Table} from "react-bootstrap"

class SpecificMarket extends Component{

    constructor(props){
        super(props);
        this.presentation_style = {
            "marginTop": "2%",
            "marginLeft": "100%",
            "width": "100%"
        };
        this.state = {
            "market_data" : []
        };
        this.presentation = "";
        this.delay = 800;
        // this.connect_data = this.connect_data.bind(this)
        // this.show_data = this.show_data.bind(this);
    }


    componentDidMount() {
         let _  = anime({
            targets: '#presentation',
            translateX: -window.innerWidth/2,
            delay: this.delay

    });
         this.get_data_api();
         this.opacity_tab();

    };


    componentDidUpdate(prevProps, prevState, snapshot) {
        if (prevProps.concerned === this.props.concerned){
            return false
        }
        console.log("Update");
        let a = document.getElementById("presentation");
        console.log(a);
        a.style.removeProperty('transform');
        console.log(window.innerWidth);
        let _  = anime({
            targets: '#presentation',
            translateX: -window.innerWidth/2,
            delay: this.delay
    });
        this.get_data_api();
        this.opacity_tab();
};

    get_data_api = () => {
        this.props.endpoint.get("/market/"+this.props.concerned)
                        .then(
                        res => {
                            this.setState({
                                "market_data" : res.data
                            })
                        })
    };


    define_presentation = () => (
        <div id="presentation" style={this.presentation_style} >
                <h2 className={"mainTitle"}>{this.props.concerned}</h2>
                <div className={"images"}>
                    <img alt="" src={this.props.img+this.props.concerned.substring(0,2)+"/flat/64.png"}/>
                    <img alt={""} src={this.props.img+this.props.concerned.substring(3,5)+"/flat/64.png"}/>
                </div>
            </div>

    );


    sleep = time => {
        return new Promise((resolve) => setTimeout(resolve, time));
    };

    opacity_tab = () => {
            this.sleep(this.delay);
            let opac = document.getElementById("table");
            opac.style.opacity = 0;
            let i = 0;
            let interval = window.setInterval(
                    () => {
                    if (opac.style.opacity > 1){
                        clearInterval(interval);
                    }
                    else {
                        opac.style.opacity = i/10;
                        i ++;

                    }
                    }
                        , this.delay/4);

        };


    render() {

        const show_data = () => (
                        this.state.market_data.map(

                            elt => {
                            let params = {
                                "value":"Buy",
                                "style":{
                                    "color":"green",
                                    "fontWeight":"bold"
                                }
                            };
                            if (elt.position_type ==="S"){
                                params.style.color = "red";
                                params.value = "Sell";
                            }
                            // let date = new Date(elt.dayout_market+"T"+elt.timeout_market);
                            return(
                                <tr key={elt.id}>
                                    <td style={params.style}>{params.value}</td>
                                    <td>{elt.stepin_market.split("-")[0]}</td>
                                    <td>{0}</td>
                                    <td>{elt.result_percent}</td>
                                </tr>
                              )}));

        return(
            <div>
                {this.define_presentation()}
                <Table id="table" responsive="sm" >
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th> Time In </th>
                            <th> Time Out </th>
                            <th> Result(%) </th>
                        </tr>
                    </thead>
                    <tbody>
                    {show_data()}
                    </tbody>
                </Table>
            </div>
        );
    }
}
export default SpecificMarket;