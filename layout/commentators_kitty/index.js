LoadEverything().then(() => {

    let scoreboardNumber = 1;
    
    gsap.config({ nullTargetWarn: false, trialWarn: false });

  
    Start = async () => {
    };
  
    Update = async (event) => {
      let data = event.data;
      let oldData = event.oldData;
  
      for (const [index, commentator] of Object.values(
        data.commentary
      ).entries()) {
        if (commentator) {
                SetInnerHtml(
                    $(`.p${index + 1}.comm-name`), `${commentator.name}`
                  );

            SetInnerHtml($(`.p${index + 1}.twitter`), `${commentator.twitter}`)

            SetInnerHtml($(`.p${index + 1}.pronouns`), `${commentator.pronoun}`)
        }
      }
    };
  });