LoadEverything().then(() => {

    let scoreboardNumber = 1;
    
    gsap.config({ nullTargetWarn: false, trialWarn: false });

  
    Start = async () => {
    };
  
    Update = async (event) => {
      let data = event.data;
      let oldData = event.oldData;
  
      if (Object.keys(data.score[scoreboardNumber].team["1"].player).length == 1) {
        for (const [t, team] of [
          data.score[scoreboardNumber].team["1"],
          data.score[scoreboardNumber].team["2"],
        ].entries()) {
          for (const [p, player] of [team.player["1"]].entries()) {
            if (player) {
              SetInnerHtml(
                $(`.p${t + 1}.player-name`), `${player.name}`
              );

              SetInnerHtml(
                $(`.p${t + 1}.twitter`), `${player.twitter}`
              );

              SetInnerHtml(
                $(`.p${t + 1}.pronouns`), `${player.pronoun}`
              );

              SetInnerHtml(
                $(`.p${t + 1}.seed`), player.seed ? `${player.seed}` : ``
              );
  
              SetInnerHtml($(`.p${t + 1}.score-text`), String(team.score));
            }
          }
        }
      }
    };
  });
  