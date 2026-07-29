import polars as pl
from plotnine import *

# load df
df = pl.read_csv("nba_team_salaries.csv")

# create R^2 column
def make_r2_labels(df, y_col):
    """Compute R^2 per year for a given y variable (Wins or NetRating)."""
    return (
        df.group_by("Year")
        .agg(
            pl.corr("Salary", y_col).pow(2).alias("r2")
        )
        .with_columns(
            pl.col("r2").round(3).cast(pl.Utf8).alias("label")
        )
    )

# make R^2 plots
def make_plot(df, y_col, y_label, title):
    r2_df = make_r2_labels(df, y_col)

    # position labels near the top-left of each facet
    label_positions = (
        df.group_by("Year")
        .agg([
            pl.col("Salary").min().alias("x_pos"),
            pl.col(y_col).max().alias("y_pos"),
        ])
        .join(r2_df, on="Year")
        .with_columns(
            ("R² = " + pl.col("label")).alias("r2_text")
        )
    )

    p = (
        ggplot(df, aes("Salary", y_col))
        + geom_point(alpha=0.6, size=1.5)
        + geom_smooth(method="lm", color="#366191", se=False)
        + geom_text(
            data=label_positions,
            mapping=aes(x="x_pos", y="y_pos", label="r2_text"),
            ha="left", va="top", size=7, color="black"
        )
        + facet_wrap("Year", scales="free", nrow=3, ncol=4)
        + theme_minimal(base_family="sans-serif")
        + theme(
            legend_position="none",
            panel_background=element_rect(fill="floralwhite"),
            plot_background=element_rect(fill="floralwhite", color="floralwhite"),
            plot_title=element_text(size=16, face="bold", hjust=0.5),
            plot_subtitle=element_text(color="#a6a6a6", margin={"t": 2.5, "b": 10}, size=7, hjust=0.5),
            strip_text=element_text(face="bold", size=9),
            axis_text=element_text(size=5),
            panel_spacing_y=0.05,
            panel_spacing_x=0.01
        )
        + scale_x_continuous(
            breaks=[50_000_000, 100_000_000, 150_000_000, 200_000_000],
            labels=lambda l: [f"${v/1e6:.0f}M" for v in l]
        )
        + labs(
            x="Team Salary",
            y=y_label,
            title=title,
            subtitle=f"R² measures the proportion of variance in {f"{y_label}"} explained by Salary",
        )
    )
    return p

# plot wins vs salary
p_wins = make_plot(df, "W", "Regular Season Wins", "Team Salary vs Wins")
p_wins.save('salary_vs_wins.png', dpi=300)
p_wins.show()

# plot net rating vs salary
p_rating = make_plot(df, "NetRating", "Net Rating", "Team Salary vs Net Rating")
p_rating.save('salary_vs_netrating.png', dpi=300)
p_rating.show()



# make plots with luxury tax threshold and champion
def make_plot_tax(df, y_col, y_label, title):
    # data for vertical luxury tax lines
    vline_data = df.select(["Year", "LuxuryTax"]).unique()

    # flag whether each row's team was that season's champion
    df = df.with_columns(
        (pl.col("Team") == pl.col("Champion")).alias("is_champion")
    )

    p = (
        ggplot(df, aes("Salary", y_col))
        + geom_vline(
            data=vline_data,
            mapping=aes(xintercept="LuxuryTax"),
            color="#a6a6a6", linetype="dashed", size=0.5
        )
        + geom_point(
            df.filter(~pl.col("is_champion")),
            aes("Salary", y_col),
            alpha=0.6, size=1.5, color="black"
        )
        + geom_point(
            df.filter(pl.col("is_champion")),
            aes("Salary", y_col),
            alpha=0.8, size=1.5, color="#D4AF37"  # gold
        )
        + scale_x_continuous(
            breaks=[100_000_000, 200_000_000],
            labels=lambda l: [f"${v/1e6:.0f}M" for v in l]
        )
        + facet_wrap("Year", scales="free", nrow=3, ncol=4)
        + theme_minimal(base_family="sans-serif")
        + theme(
            legend_position="none",
            panel_background=element_rect(fill="floralwhite"),
            plot_background=element_rect(fill="floralwhite", color="floralwhite"),
            plot_title=element_text(size=16, face="bold", hjust=0.5),
            plot_subtitle=element_text(color="#a6a6a6", margin={"t": 2.5, "b": 10}, size=9, hjust=0.5),
            strip_text=element_text(face="bold", size=12),
            axis_text=element_text(size=5),
            #figure_size=(11, 9),
            panel_spacing_y=0.05,
            panel_spacing_x=0.01
        )
        + labs(
            x="Team Salary",
            y=y_label,
            title=title,
            subtitle="Dashed line = luxury tax threshold, gold point = champion",
        )
    )
    return p

# plot wins vs salary
p_wins = make_plot_tax(df, "W", "Regular Season Wins", "Are winning teams more likely to spend?")
p_wins.save('salary_vs_wins_tax.png', dpi=300)
p_wins.show()

# plot net rating vs salary
p_rating = make_plot_tax(df, "NetRating", "Net Rating", "Are high-performing teams more likely to spend?")
p_rating.save('salary_vs_netrating_tax.png', dpi=300)
p_rating.show()




# compute average salary per year and grab the luxury tax value per year
yearly = (
    df.group_by("Year")
    .agg([
        pl.col("Salary").mean().alias("Avg Salary"),
        pl.col("LuxuryTax").first().alias("Luxury Tax"),
    ])
    .sort("Year")
)

# reshape to long format
yearly_long = yearly.unpivot(
    on=["Avg Salary", "Luxury Tax"],
    index=["Year"],
    variable_name="Metric",
    value_name="Value",
)

# plot luxury tax vs avg team salary YOY
p = (
    ggplot(yearly_long, aes("Year", "Value", color="Metric"))
    + geom_line(size=1.2)
    + geom_point(size=2.5, alpha=0.8)
    + scale_color_manual(values={"Avg Salary": "#704D9E", "Luxury Tax": "#D4AF37"})
    + scale_y_continuous(
        labels=lambda l: [f"${v/1e6:.0f}M" for v in l]
    )
    + scale_x_continuous(breaks=list(range(2015, 2027)))
    + theme_minimal(base_family="sans-serif")
    + theme(
        legend_position="top",
        legend_title=element_blank(),
        legend_text=element_text(size=10),
        panel_background=element_rect(fill="floralwhite"),
        plot_background=element_rect(fill="floralwhite", color="floralwhite"),
        plot_title=element_text(size=18, face="bold", hjust=0.5),
        plot_subtitle=element_text(color="#a6a6a6", margin={"t": 4, "b": 14}, size=10, hjust=0.5),
        axis_text=element_text(size=9),
        axis_title=element_text(size=11),
        axis_text_x=element_text(rotation=45, ha="right"),
        figure_size=(10, 6),
        dpi=150,
    )
    + labs(
        x="Season",
        y="Value",
        title="Average Team Salary vs. Luxury Tax Threshold"
    )
)

p.save('avgsalary_vs_luxurytax.png', dpi=300)
p.show()