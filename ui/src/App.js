import './App.css';
import React, { Component } from "react"

const ENDPOINT = "localhost:5000";
const PRODUCER_ENDPOINT = "localhost:5001"

 
export default class App extends Component {
  constructor(props) {
    super(props);
    this.state = {
        games: {},
        gameId: "7471" // set this game as the default
    }
    this.processMessage = this.processMessage.bind(this);
    this.startGame = this.startGame.bind(this);
    this.onInputChange = this.onInputChange.bind(this);
  }

  processMessage(message) {
      message = JSON.parse(message.data)
      const game_id = message.game_id
      const newState = {...this.state, games: {...this.state.games, [game_id]: message}}
      this.setState(newState)
  }

  componentDidMount() {
    fetch("http://" + ENDPOINT + "/games")
      .then(response => response.json())
      .then(data => {
        data = JSON.parse(data)
        const result = data.reduce(function(map, obj) {
          map[obj.game_id] = obj; return map;
        }, {})
        this.setState({...this.state, games: result})
      })

    const client = new WebSocket("ws://" + ENDPOINT + "/ws")

    client.onopen = function(event) {
      console.log("Connected!")
    }
 
    client.onerror = function(error) {
      console.log(error)
    };
    
    client.onmessage = this.processMessage

    client.oclose = function(event) {
      console.log("Disconnected")
    }
  };

  onInputChange(event) {
    this.setState({ ...this.state, gameId: event.target.value });
  }

  startGame() {
    const url = "http://" + PRODUCER_ENDPOINT + "/games/" + this.state.gameId
    const requestOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    };
    fetch(url, requestOptions)
      .then(response => console.log(response));
  }

  render() {
    return (
      <div style={{marginLeft: 50}}>
        <h1>Live football Scores</h1>
        {Object.keys(this.state.games).map((key) => <Game key={key} game={this.state.games[key]}/>)}
        <h2>Admin Panel</h2>
        <input
          value={ this.state.gameId }
          onChange={ this.onInputChange }
        />
        <button onClick={this.startGame}>Start events!</button>
      </div>
    );
  }
}

const Game = (props) => {
  var home_team = "Unknown"
  var away_team = "Unknown"
  if (props.game.home_team) {
    home_team = props.game.home_team.name
  }
  if (props.game.away_team) {
    away_team = props.game.away_team.name
  }

  const home_goals = props.game.goals.reduce(function(amount, goal) {
    if (goal.team_id === props.game.home_team.id){
      amount += 1;
    } 
    return amount
  }, 0)

  const away_goals = props.game.goals.reduce(function(amount, goal) {
    if (goal.team_id === props.game.away_team.id){
      amount += 1;
    } 
    return amount
  }, 0)

  return <div style={{margin: 10}}>
    {home_team} - {away_team}: {home_goals}-{away_goals}
    <br/>
    <div style={{paddingLeft: 10, fontSize: 12}}>
    {props.game.goals.map((item) => 
      <div key={item.minute.toString()+item.player.id}>Goal: {item.player.name} - {item.minute}'</div>)}
    {props.game.yellow_cards.map((item) => 
      <div key={item.minute.toString()+item.player.id}>Yellow: {item.player.name} - {item.minute}'</div>)}
    {props.game.second_yellows.map((item) => 
      <div key={item.minute.toString()+item.player.id}>Second yellow: {item.player.name} - {item.minute}'</div>)}
    {props.game.red_cards.map((item) => 
      <div key={item.minute.toString()+item.player.id}>Red: {item.player.name} - {item.minute}'</div>)}
    </div>
  </div>
}
