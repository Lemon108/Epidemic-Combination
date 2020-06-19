import React, { Component } from 'react';
import Logo from '../../asserts/logo.jpg';
import Img from '../../asserts/image/logo.svg';
import SildeShow from './ImgFlow';
import '../../asserts/css/NewMain.css'
import { List, Typography, Divider } from 'antd';

class NewsMain extends Component {
    constructor(props) {
        super(props);
        this.state = {
            data:[
                {title:'新闻一'},
                {title:'新闻二'},
                {title:'新闻三'},
            ]
        };
    }

    render() {
        return (
            <div>
                <List 
                    header = {<div>疫情新闻</div>}
                    bordered
                    dataSource = {this.state.data}
                    renderItem = {item=>(
                        <List.Item>
                            <List.Item.Meta
                                title = {<a>{item.title}</a>}>
                            </List.Item.Meta>
                        </List.Item>
                    )}>
                </List>
                <div className = "NewMain">
                    <SildeShow>
                        <img src = {Logo}></img>
                        <img src = {Img}></img>
                        <img src = {Logo}></img>
                    </SildeShow>
                </div>
            </div>
        );
    }
}

export default NewsMain;
