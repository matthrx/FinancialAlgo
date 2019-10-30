import React, {Component} from "react";
import {Table} from "react-bootstrap";
import { IoIosBookmarks } from 'react-icons/io';
class Historical extends Component{

    constructor(props){
        super(props);
        this.state = {
            'historical' : []

    }}

    componentDidMount() {
        this.props.endpoint.get("/historical")
            .then(
                res => {
                    this.setState({
                        'historical' : res.data
                    });
                }
            )
    }



    render(){
        const print_historical_data = () => {
            console.log(this.state.historical);
            return (this.state.historical.map(
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
                let date = new Date(elt.dayout_market+"T"+elt.timeout_market);

                return(
                    <tr key={elt.id}>
                        <td>{elt.market}</td>
                        <td style={params.style}>{params.value}</td>
                        <td>{elt.stepin_market.split("-")[0]}</td>
                        <td>{date.toString().split("GMT")[0]}</td>
                        <td>{elt.result_percent}</td>
                </tr>
                );
            }))};

        const style_div = {
                "marginTop": "2%",
                "marginBotton": "2%"
            };

        return(

            <div>
                <h1 style={style_div}>Historical <IoIosBookmarks/></h1>
                <Table responsive="sm">
                        <thead>
                            <tr>
                                <th>Market</th>
                                <th>Type</th>
                                <th> Time In </th>
                                <th> Time Out </th>
                                <th> Result(%) </th>
                            </tr>
                        </thead>
                        <tbody>
                        {print_historical_data()}
                        </tbody>
                </Table>
            </div>
        );
    }
}
export default Historical;