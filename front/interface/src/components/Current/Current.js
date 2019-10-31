import React, {Component} from "react"
import {Table} from "react-bootstrap"
import axios from 'axios';
import {IoMdArrowUp, IoMdArrowForward, IoMdArrowDown} from "react-icons/io";

class Current extends Component{

    constructor(props){
        super(props);
        this.state={
            forex_url : "https://financialmodellingprep.com/api/v3/forex/",
            current_result : {},
            color_state : {},
            symbol : {}
        };
        this.r = axios.create();
        this.interval = "";

        }



    get_all_current = () => {
        return ( this.props.data.map(
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
                return(
                     <tr>
                        <td>{elt.market}</td>
                        <td style={params.style}>{params.value}</td>
                        <td>{elt.stepin_market.split("-")[0]}</td>
                        <td>{elt.stepin_value}</td>
                         <td id={elt.market}>{this.state.symbol[elt.market]}{this.state.current_result[elt.market]}</td>
                    </tr>
                );
            }))};

    update_current_price = () => {
        this.props.data.map(
               elt => {
                    this.r.get(this.state.forex_url+elt.market)
                    .then(
                    response => {
                        console.log(response.data);
                        let element = {...this.state.current_result};
                        let intermediate_value;
                        let color_values = {...this.state.color_state};
                        if (elt.position_type === "S") {
                            intermediate_value = (((elt.stepin_value - response.data.ask)/elt.stepin_value)*100).toFixed(6);
                        }
                        else {
                             intermediate_value = (((response.data.ask - elt.stepin_value)/elt.stepin_value)*100).toFixed(6);
                        }
                        let tempotary_symbol = {...this.state.symbol};
                        if (intermediate_value > element[elt.market]){
                                color_values[elt.market] = "green";
                                tempotary_symbol[elt.market] = <IoMdArrowUp name="arrow" className={"green"}/>
                            }
                        else if (intermediate_value === element[elt.market]){
                                color_values[elt.market] = "gray";
                                tempotary_symbol[elt.market] = <IoMdArrowForward name="arrow" className={"gray"}/>
                            }
                        else if(intermediate_value < element[elt.market]){
                            color_values[elt.market] = "red";
                            tempotary_symbol[elt.market] = <IoMdArrowDown name = "arrow" className={"red"}/>
                            }

                        element[elt.market] =  intermediate_value;
                        this.setState(
                            {
                                "current_result" : element,
                                "color_state" : color_values,
                                "symbol": tempotary_symbol
                            }
                        );
                    }
                )
                    .catch(
                    err => {
                            console.error(err);
                    }
                   );})};


    sleep = time => {
        return new Promise((resolve) => setTimeout(resolve, time));
    };

    componentDidMount() {
        this.update_current_price();
        this.interval = setInterval(this.update_current_price, 10000);
    }

    componentWillUnmount() {
       clearInterval(this.interval);
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
       if (prevState.current_result === this.state.current_result){
           this.update_current_price();
           return false;
       }

   }

    render(){
        let a = Object.keys(this.state.current_result);
        let arrows = [];
        a.map(
            each_key => {
                arrows = document.getElementsByName("arrow");
                for (var item of arrows){
                            item.style.visibility = "visible";
                        }
                let element = document.getElementById(each_key);
                element.style.color = this.state.color_state[each_key];
                element.style.fontWeight = "bold";
                this.sleep(4000).then(
                    () => {
                        element.style.color = "black";
                        element.style.fontWeight = "normal";

                        for (var item of arrows){
                            item.style.visibility = "hidden";
                        }


                    }
            )}
        );
        console.log(this.get_all_current());

        return(
                <Table responsive={"sm"}>
                     <thead>
                         <tr>
                             <th>Market</th>
                             <th> Type </th>
                             <th> Time </th>
                             <th> Value </th>
                             <th> Result(%) </th>
                         </tr>
                     </thead>
                    <tbody>
                        {this.get_all_current()}
                    </tbody>

                </Table>

        );
    }

}
export default Current;