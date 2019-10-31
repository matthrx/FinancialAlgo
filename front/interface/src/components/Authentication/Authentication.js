import React, {useEffect} from "react";
import clsx from 'clsx';
import { makeStyles } from '@material-ui/core/styles';
import Visibility from '@material-ui/icons/Visibility';
import VisibilityOff from '@material-ui/icons/VisibilityOff';
import InputLabel from '@material-ui/core/InputLabel';
import FormControl from "@material-ui/core/FormControl";
import Input from '@material-ui/core/Input';
import InputAdornment from '@material-ui/core/InputAdornment';
import IconButton from '@material-ui/core/IconButton';
import TextField from "@material-ui/core/TextField";
import Button from "@material-ui/core/Button";
import "./Authentication.css"
import axios from "axios";
import {Redirect} from "react-router-dom"

const useStyles = makeStyles(theme => ({
  root: {
    display: 'flex',
    flexWrap: 'wrap',

  },
  margin: {
    marginTop: theme.spacing(3),
  },
  withoutLabel: {
    marginTop: theme.spacing(3),
  },
  textField: {
    width: 200,
  },
    button : {
       marginTop: theme.spacing(2)
    }
    }));

export default function Authentification(){

     const classes = useStyles();
     const [values, setValues] = React.useState({
            username : '',
            password: '',
            showPassword: false,
  });
     let r = axios.create();
     let error = false;
     r.defaults.baseURL = "http://127.0.0.1:8000/api";
     localStorage.clear();

         const handleChange = prop => event => {
            setValues({ ...values, [prop]: event.target.value });

        };

         useEffect(
             () => {
                 let button = document.getElementById("button");
                 if (values["username"] !== "" && values["password"] !== "" && button.disabled === true){
                     button.disabled = false;
                     button.classList.remove("Mui-disabled");

                 }
                 else if (values["username"] === "" || values["password"] === ""){
                     button.disabled = true;
                     button.classList.add("Mui-disabled");
                 }
             }, [values]
         );

        const handleClickShowPassword = () => {
        setValues({ ...values, showPassword: !values.showPassword });
        };

        const handleMouseDownPassword = event => {
            event.preventDefault();
        };


         const sleep = time => {
                        return new Promise((resolve) => setTimeout(resolve, time));
                        };

        const getToken = () => {
            r.get("/token?username="+values["username"]+"&password="+values["password"])
                .then(
                    (res) => {
                        console.log("Next page");
                        localStorage.setItem("token", res.data.token);
                        console.log(res.data.exp);
                        setTimeout(
                            () => {
                                localStorage.removeItem("token");
                            }
                        ,res.data.exp);
                        window.location = window.location.href.toString()+"menu"
                    })
                .catch(
                    _ => {

                        const textfield = document.getElementById("standard-basic");
                        const password = document.getElementById("standard-adornment-password");
                        const form = document.getElementsByTagName("form")[0];
                        const incorrect = document.getElementById("incorrect");
                        incorrect.style.visibility = "visible";
                        form.style.border = "5px solid red";
                        form.classList.add("wiggle");
                        textfield.value = "";
                        password.value = "";
                        values["password"] = "";
                        values["username"] = "";
                        error = true;
                         sleep(3000).then(
                             () => {
                                 incorrect.style.visibility = "hidden";
                                 form.style.border = "";
                                 form.classList.remove("wiggle");
                             })
                    })

                    };



        return(
            <div className={"authentication bg-dark"}>
                <form className={"printForm"}>
                    <h2> SIGN IN </h2>
                <div id="inputs" className={classes.root}>
                     <TextField
                          id="standard-basic"
                          className={clsx(classes.textField, classes.margin)}
                          label="Username"
                          margin="normal"
                          onChange={handleChange('username')}
                        />
                     <FormControl className={clsx(classes.margin, classes.textField)}>
                          <InputLabel htmlFor="standard-adornment-password">Password</InputLabel>
                          <Input
                            id="standard-adornment-password"
                            type={values.showPassword ? 'text' : 'password'}
                            value={values.password}
                            onChange={handleChange('password')}
                            endAdornment={
                              <InputAdornment position="end">
                                <IconButton
                                  aria-label="toggle password visibility"
                                  onClick={handleClickShowPassword}
                                  onMouseDown={handleMouseDownPassword}
                                >
                                  {values.showPassword ? <Visibility /> : <VisibilityOff />}
                                </IconButton>
                              </InputAdornment>
                            }
                          />
                     </FormControl>

                </div>
                    <span id={"incorrect"}> Incorrect Credentials </span>
                    <div>
                    <Button id="button" variant="outlined" color="inherit" className={classes.button}
                     onClick={getToken} >
                        Submit
                    </Button>
                    </div>
                </form>
            </div>
        );
    }

